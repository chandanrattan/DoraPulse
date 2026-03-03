# DoraPulse Composite Action

Reusable GitHub Composite Action to calculate DORA metrics and upload CSV artifacts.

## Understanding DORA Metrics

DoraPulse calculates the four key metrics defined by the DORA (DevOps Research and Assessment) team.

### Deployment Frequency

- How often an organization successfully releases to production
- Elite performers: Multiple deployments per day
- Metric shows: Release cadence and batch size

### Lead Time for Changes

- Time taken from code commit to code running in production
- Elite performers: Less than one hour
- Metric shows: Process efficiency and deployment pipeline health

### Mean Time to Recovery (MTTR)

- How long it takes to restore service after an incident
- Elite performers: Less than one hour
- Metric shows: Incident response effectiveness

### Change Failure Rate

- Percentage of changes that lead to degraded service
- Elite performers: 0-15%
- Metric shows: Quality of testing and review processes

## References

- [Official DORA Research Program](https://www.devops-research.com/research.html)
- [Google Cloud's DORA Metrics](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
- [DORA's State of DevOps Reports](https://www.devops-research.com/research.html#reports)
- [DORA Metrics in GitHub](https://resources.github.com/devops/tools/dora-metrics/)
- [Accelerate: The Science of Lean Software](https://books.google.com/books?id=Kax-DwAAQBAJ) - The book that introduced DORA metrics

## Outputs

- `dora_metrics.csv`: per-repository metrics
- `dora_metrics_summary.csv`: aggregate summary

## Inputs

- `token` (required): GitHub token with read access to target repositories
- `owner` (optional): repository owner for single repository mode, or optional owner/org filter in topic mode
- `repo` (optional): repository name for single repository mode
- `topic` (optional): GitHub topic for discovery mode
- `days` (optional, default `30`)
- `artifact_name` (optional, default `dora-metrics-csv`)

Provide either:
- `owner` + `repo` (single repository mode), or
- `topic` (topic mode, optional `owner` filter)

## DORA Calculation Logic

Metrics are calculated from closed pull requests with `merged_at` inside the selected rolling window (`days`).

- Deployment Frequency:
`merged_prs_in_window / days`
- Lead Time for Changes (hours):
Average of `(merged_at - created_at)` for merged PRs in window
- MTTR (hours):
Average of `(merged_at - created_at)` only for merged PRs whose title/body contains recovery keywords: `fix`, `hotfix`, `revert`, `rollback`
- Change Failure Rate (%):
`(failed_prs / merged_prs_in_window) * 100`
A PR is treated as failed if title/body contains any failure keyword: `fix`, `hotfix`, `revert`, `rollback`, `emergency`

CSV files:

- `dora_metrics.csv`:
One row per repository with columns: `repository`, `period_days`, `merged_prs`, `failed_prs`, `deployment_frequency_per_day`, `lead_time_hours`, `mttr_hours`, `change_failure_rate_pct`
- `dora_metrics_summary.csv`:
Columns: `repositories_analyzed`, `period_days`, `total_merged_prs`, `total_failed_prs`, `avg_deployment_frequency_per_day`, `avg_lead_time_hours`, `avg_mttr_hours`
Weighted failure rate formula: `weighted_change_failure_rate_pct = (total_failed_prs / total_merged_prs) * 100`

Notes:

- Unmerged PRs are ignored for all four metrics.
- If no merged PRs are found in window, rate/time metrics are emitted as `0.0`.

## Usage (Single Repo)

```yaml
name: DORA Metrics

on:
  workflow_dispatch:

jobs:
  dora:
    runs-on: ubuntu-latest
    steps:
      - name: Run DoraPulse
        uses: chandanrattan/DoraPulse@main
        with:
          token: ${{ secrets.TOKEN }}
          owner: my-org
          repo: my-service
          days: 30
          artifact_name: my-service-dora
```

## Usage (Topic Mode)

```yaml
name: DORA Topic Metrics

on:
  workflow_dispatch:

jobs:
  dora-topic:
    runs-on: ubuntu-latest
    steps:
      - name: Run DoraPulse
        uses: chandanrattan/DoraPulse@main
        with:
          token: ${{ secrets.TOKEN }}
          topic: microservice
          owner: my-org
          days: 30
```

## Local Script

The action uses `scripts/dora_metrics_csv.py`.

### Run Locally

1. Install dependencies:

```bash
pip install .
```

2. Copy env template and set values:

```bash
cp .env.example .env
```

3. Edit `.env` and choose one mode:
- Single repository mode: set `TOKEN`, `DORA_OWNER`, `DORA_REPO` and keep `DORA_TOPIC` empty
- Topic mode: set `TOKEN`, `DORA_TOPIC` and optionally `DORA_OWNER` as filter; keep `DORA_REPO` empty

4. Run:

```bash
python scripts/dora_metrics_csv.py
```

Optional examples:

```bash
# Estimate only (no CSV generation)
python scripts/dora_metrics_csv.py --estimate-only

# CLI override example
python scripts/dora_metrics_csv.py --owner my-org --repo my-service --token <token>
```

Install with dev tooling:

```bash
pip install ".[dev]"
```

For local execution:

```bash
python scripts/dora_metrics_csv.py
```

Use `.env` / `.env.example` variables:

- `TOKEN`
- `DORA_OWNER` + `DORA_REPO`, or `DORA_TOPIC`
- `DORA_DAYS`
- `DORA_OUT_DIR`
