#!/usr/bin/env python3
"""Generate DORA metrics as CSV for a single repo or repositories by GitHub topic."""

from __future__ import annotations

import argparse
import csv
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple
from dotenv import load_dotenv

GITHUB_API_URL = "https://api.github.com"
FAILURE_KEYWORDS = ("fix", "hotfix", "revert", "rollback", "emergency")
RECOVERY_KEYWORDS = ("fix", "hotfix", "revert", "rollback")
DEFAULT_DOTENV_PATH = ".env"


@dataclass
class RepoMetrics:
    repository: str
    period_days: int
    merged_prs: int
    failed_prs: int
    deployment_frequency_per_day: float
    lead_time_hours: float
    mttr_hours: float
    change_failure_rate_pct: float


class GitHubAPIError(RuntimeError):
    pass


class GitHubAPI:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GitHub token is required")
        self.token = token
        self.request_count = 0
        self.total_request_seconds = 0.0
        self.topic_search_pages = 0

    def _request_url(self, url: str) -> Tuple[object, Dict[str, str]]:
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req) as response:
                import json

                payload = json.loads(response.read().decode("utf-8"))
                headers = {k.lower(): v for k, v in response.headers.items()}
                self.request_count += 1
                self.total_request_seconds += time.perf_counter() - started
                return payload, headers
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise GitHubAPIError(f"GitHub API error {exc.code} for {url}: {body}") from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"Network error while calling {url}: {exc}") from exc

    def _request(self, path: str, params: Optional[Dict[str, str]] = None) -> Tuple[object, Dict[str, str]]:
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params)
        url = f"{GITHUB_API_URL}{path}{query}"
        return self._request_url(url)

    @staticmethod
    def _next_url_from_link_header(link_header: Optional[str]) -> Optional[str]:
        if not link_header:
            return None
        parts = [segment.strip() for segment in link_header.split(",")]
        for part in parts:
            if 'rel="next"' in part:
                start = part.find("<")
                end = part.find(">")
                if start != -1 and end != -1:
                    return part[start + 1 : end]
        return None

    @staticmethod
    def _last_page_from_link_header(link_header: Optional[str]) -> Optional[int]:
        if not link_header:
            return None
        parts = [segment.strip() for segment in link_header.split(",")]
        for part in parts:
            if 'rel="last"' in part:
                start = part.find("<")
                end = part.find(">")
                if start == -1 or end == -1:
                    continue
                url = part[start + 1 : end]
                parsed = urllib.parse.urlparse(url)
                page_values = urllib.parse.parse_qs(parsed.query).get("page")
                if page_values:
                    try:
                        return int(page_values[0])
                    except ValueError:
                        return None
        return None

    def get_repo(self, full_name: str) -> Dict[str, object]:
        payload, _ = self._request(f"/repos/{full_name}")
        if not isinstance(payload, dict):
            raise GitHubAPIError(f"Unexpected repo response for {full_name}")
        return payload

    def search_repositories_by_topic(self, topic: str, owner: Optional[str]) -> List[str]:
        q_parts = [f"topic:{topic}", "archived:false"]
        if owner:
            q_parts.append(f"user:{owner}")

        repos: List[str] = []
        page = 1
        per_page = 100

        self.topic_search_pages = 0
        while True:
            payload, _ = self._request(
                "/search/repositories",
                {
                    "q": " ".join(q_parts),
                    "sort": "updated",
                    "order": "desc",
                    "page": str(page),
                    "per_page": str(per_page),
                },
            )

            if not isinstance(payload, dict):
                raise GitHubAPIError("Unexpected search response")
            items = payload.get("items", [])
            if not isinstance(items, list) or not items:
                break

            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("full_name")
                if isinstance(name, str):
                    repos.append(name)
            self.topic_search_pages += 1

            if len(items) < per_page:
                break
            page += 1

        return repos

    def fetch_closed_pull_requests(self, full_name: str) -> Iterable[Dict[str, object]]:
        next_url = f"{GITHUB_API_URL}/repos/{full_name}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page=1"

        while next_url:
            payload, headers = self._request_url(next_url)
            if not isinstance(payload, list):
                raise GitHubAPIError(f"Unexpected pull request response for {full_name}")
            for pr in payload:
                if isinstance(pr, dict):
                    yield pr
            next_url = self._next_url_from_link_header(headers.get("link"))

    def estimate_closed_pr_count(self, full_name: str) -> int:
        payload, headers = self._request(
            f"/repos/{full_name}/pulls",
            {"state": "closed", "sort": "updated", "direction": "desc", "per_page": "1", "page": "1"},
        )
        if not isinstance(payload, list):
            raise GitHubAPIError(f"Unexpected pull request response for {full_name}")
        if not payload:
            return 0
        last_page = self._last_page_from_link_header(headers.get("link"))
        if last_page is None:
            return len(payload)
        return last_page


def parse_iso8601(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def log_info(message: str) -> None:
    print(f"ℹ️ {message}")


def log_step(message: str) -> None:
    print(f"🔹 {message}")


def log_done(message: str) -> None:
    print(f"✅ {message}")


def text_contains_keywords(text: str, keywords: Tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in keywords)


def calculate_repo_metrics(prs: Iterable[Dict[str, object]], period_days: int) -> RepoMetrics:
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    merged_prs: List[Dict[str, object]] = []
    lead_times: List[float] = []
    recovery_times: List[float] = []
    failed_deployments = 0

    for pr in prs:
        merged_at_raw = pr.get("merged_at")
        if not isinstance(merged_at_raw, str):
            continue

        merged_at = parse_iso8601(merged_at_raw)
        if merged_at < cutoff:
            continue

        created_at_raw = pr.get("created_at")
        if not isinstance(created_at_raw, str):
            continue
        created_at = parse_iso8601(created_at_raw)

        merged_prs.append(pr)
        lead_times.append(max((merged_at - created_at).total_seconds() / 3600.0, 0.0))

        title = str(pr.get("title") or "")
        body = str(pr.get("body") or "")
        blob = f"{title}\n{body}"

        if text_contains_keywords(blob, FAILURE_KEYWORDS):
            failed_deployments += 1

        if text_contains_keywords(blob, RECOVERY_KEYWORDS):
            recovery_times.append(max((merged_at - created_at).total_seconds() / 3600.0, 0.0))

    merged_count = len(merged_prs)
    lead_time = statistics.fmean(lead_times) if lead_times else 0.0
    mttr = statistics.fmean(recovery_times) if recovery_times else 0.0
    deployment_frequency = (merged_count / float(period_days)) if period_days > 0 else 0.0
    cfr = ((failed_deployments / float(merged_count)) * 100.0) if merged_count > 0 else 0.0

    return RepoMetrics(
        repository="",
        period_days=period_days,
        merged_prs=merged_count,
        failed_prs=failed_deployments,
        deployment_frequency_per_day=deployment_frequency,
        lead_time_hours=lead_time,
        mttr_hours=mttr,
        change_failure_rate_pct=cfr,
    )


def write_repo_metrics_csv(path: str, rows: List[RepoMetrics]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "repository",
                "period_days",
                "merged_prs",
                "failed_prs",
                "deployment_frequency_per_day",
                "lead_time_hours",
                "mttr_hours",
                "change_failure_rate_pct",
            ]
        )
        for item in rows:
            writer.writerow(
                [
                    item.repository,
                    item.period_days,
                    item.merged_prs,
                    item.failed_prs,
                    f"{item.deployment_frequency_per_day:.4f}",
                    f"{item.lead_time_hours:.2f}",
                    f"{item.mttr_hours:.2f}",
                    f"{item.change_failure_rate_pct:.2f}",
                ]
            )


def write_summary_csv(path: str, rows: List[RepoMetrics]) -> None:
    repo_count = len(rows)
    total_merged = sum(item.merged_prs for item in rows)
    total_failed = sum(item.failed_prs for item in rows)
    avg_deployment = statistics.fmean([item.deployment_frequency_per_day for item in rows]) if rows else 0.0
    avg_lead = statistics.fmean([item.lead_time_hours for item in rows]) if rows else 0.0
    avg_mttr = statistics.fmean([item.mttr_hours for item in rows]) if rows else 0.0
    weighted_cfr = ((total_failed / float(total_merged)) * 100.0) if total_merged > 0 else 0.0
    period_days = rows[0].period_days if rows else 0

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "repositories_analyzed",
                "period_days",
                "total_merged_prs",
                "total_failed_prs",
                "avg_deployment_frequency_per_day",
                "avg_lead_time_hours",
                "avg_mttr_hours",
                "weighted_change_failure_rate_pct",
            ]
        )
        writer.writerow(
            [
                repo_count,
                period_days,
                total_merged,
                total_failed,
                f"{avg_deployment:.4f}",
                f"{avg_lead:.2f}",
                f"{avg_mttr:.2f}",
                f"{weighted_cfr:.2f}",
            ]
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate DORA metrics CSV for GitHub repositories")
    parser.add_argument("--owner", help="Owner for single repository mode, or optional owner filter in topic mode")
    parser.add_argument("--repo", help="Repository name for single repository mode")
    parser.add_argument("--topic", help="GitHub topic to search repositories by")

    parser.add_argument("--token", help="GitHub token with repo read access")
    parser.add_argument("--days", type=int, help="Rolling window in days (default: 30)")
    parser.add_argument("--out-dir", help="Output directory for CSV files (default: artifacts)")
    parser.add_argument(
        "--estimate-seconds-per-request",
        type=float,
        default=0.35,
        help="Estimated latency per GitHub API request in seconds (default: 0.35)",
    )
    parser.add_argument(
        "--estimate-sample-size",
        type=int,
        default=10,
        help="Number of repositories sampled for runtime estimate (default: 10)",
    )
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="Print runtime estimate only and exit without generating CSVs",
    )
    return parser


def main() -> int:
    load_dotenv(dotenv_path=DEFAULT_DOTENV_PATH)
    parser = build_parser()
    args = parser.parse_args()

    token = (
        args.token
        or os.getenv("TOKEN")
        or os.getenv("DORA_GITHUB_TOKEN")
        or os.getenv("GITHUB_TOKEN")
    )
    owner = args.owner or os.getenv("DORA_OWNER")
    repo = args.repo or os.getenv("DORA_REPO")
    topic = args.topic or os.getenv("DORA_TOPIC")
    out_dir = args.out_dir or os.getenv("DORA_OUT_DIR") or "artifacts"
    repo_full_name = f"{owner}/{repo}" if owner and repo else None

    days_value = args.days if args.days is not None else os.getenv("DORA_DAYS", "30")
    try:
        days = int(days_value)
    except (TypeError, ValueError):
        parser.error("--days (or DORA_DAYS) must be an integer")

    if not token:
        parser.error("token is required. Provide --token or set TOKEN in .env")
    if topic and repo:
        parser.error("topic mode cannot be combined with --repo (or DORA_REPO)")
    if not topic and not repo_full_name:
        parser.error("single repository mode requires both --owner and --repo (or DORA_OWNER and DORA_REPO)")

    if days <= 0:
        parser.error("--days must be greater than 0")
    if args.estimate_seconds_per_request <= 0:
        parser.error("--estimate-seconds-per-request must be greater than 0")
    if args.estimate_sample_size <= 0:
        parser.error("--estimate-sample-size must be greater than 0")

    api = GitHubAPI(token)
    log_info(f"Mode: {'repo' if repo_full_name else 'topic'}")
    log_info(f"Days window: {days}")
    log_info(f"Output directory: {out_dir}")

    if repo_full_name:
        repositories = [repo_full_name]
        log_step(f"Using single repository: {repo_full_name}")
    else:
        log_step(f"Searching repositories for topic='{topic}' owner='{owner or '*'}'")
        repositories = api.search_repositories_by_topic(topic, owner)
        log_done(f"Found {len(repositories)} repositories across {api.topic_search_pages} search page(s)")

    if not repositories:
        raise GitHubAPIError("No repositories found for the provided input")

    sample_size = min(len(repositories), args.estimate_sample_size)
    sample_repos = repositories[:sample_size]
    sampled_counts: List[int] = []
    for sample_repo in sample_repos:
        log_step(f"Sampling closed PR count for {sample_repo}")
        sampled_counts.append(api.estimate_closed_pr_count(sample_repo))
    if sampled_counts:
        log_info("Sampled closed PR counts: " + ", ".join(str(value) for value in sampled_counts))
    avg_closed_prs = statistics.fmean(sampled_counts) if sampled_counts else 0.0
    estimated_pr_pages_per_repo = max(1, math.ceil(avg_closed_prs / 100.0)) if avg_closed_prs > 0 else 1
    search_requests = api.topic_search_pages if topic else 0
    estimated_total_requests = search_requests + len(repositories) + (estimated_pr_pages_per_repo * len(repositories))
    estimated_seconds = estimated_total_requests * args.estimate_seconds_per_request
    print(
        "Estimated runtime: "
        f"{estimated_seconds:.1f}s "
        f"(repos={len(repositories)}, est_requests={estimated_total_requests}, "
        f"sampled_repos={sample_size}, avg_closed_prs={avg_closed_prs:.1f})"
    )
    if args.estimate_only:
        log_done("Estimate-only mode enabled. Exiting before CSV generation.")
        return 0

    os.makedirs(out_dir, exist_ok=True)
    log_step("Starting DORA computation for repositories")

    results: List[RepoMetrics] = []
    run_started = time.perf_counter()
    total_repos = len(repositories)
    for repo in repositories:
        repo_started = time.perf_counter()
        log_step(f"Fetching repository metadata for {repo}")
        api.get_repo(repo)
        log_step(f"Fetching closed pull requests for {repo}")
        prs = api.fetch_closed_pull_requests(repo)
        metrics = calculate_repo_metrics(prs, days)
        metrics.repository = repo
        results.append(metrics)
        log_info(
            (
                f"Computed metrics for {repo}: merged_prs={metrics.merged_prs}, "
                f"failed_prs={metrics.failed_prs}, deploy_freq/day={metrics.deployment_frequency_per_day:.4f}, "
                f"lead_time_h={metrics.lead_time_hours:.2f}, mttr_h={metrics.mttr_hours:.2f}, "
                f"cfr_pct={metrics.change_failure_rate_pct:.2f}"
            ),
        )
        completed = len(results)
        repo_elapsed = time.perf_counter() - repo_started
        elapsed = time.perf_counter() - run_started
        avg_repo_seconds = elapsed / float(completed)
        eta = avg_repo_seconds * (total_repos - completed)
        print(f"[{completed}/{total_repos}] {repo} completed in {repo_elapsed:.1f}s, ETA ~{eta:.1f}s")

    repo_csv = os.path.join(out_dir, "dora_metrics.csv")
    summary_csv = os.path.join(out_dir, "dora_metrics_summary.csv")

    write_repo_metrics_csv(repo_csv, results)
    write_summary_csv(summary_csv, results)
    log_done(f"CSV written: {repo_csv}")
    log_done(f"CSV written: {summary_csv}")

    total_elapsed = time.perf_counter() - run_started
    avg_req = api.total_request_seconds / float(api.request_count) if api.request_count else 0.0
    print(
        f"Completed in {total_elapsed:.1f}s using {api.request_count} GitHub API requests "
        f"(avg request latency {avg_req:.3f}s)"
    )
    log_done(f"Wrote repository metrics to: {repo_csv}")
    log_done(f"Wrote summary metrics to: {summary_csv}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitHubAPIError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
