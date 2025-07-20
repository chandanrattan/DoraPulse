from datetime import datetime, timedelta
from collections import defaultdict

def calculate_lead_time(prs):
    """Calculate the average lead time for changes (time from code commit to code deploy)"""
    if not prs:
        return None
    lead_times = []
    for pr in prs:
        if pr.get("merged_at"):
            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            lead_times.append((merged - created).total_seconds() / 3600)  # in hours
    if lead_times:
        return sum(lead_times) / len(lead_times)
    return None

def calculate_deployment_frequency(prs, days=30):
    """Calculate deployment frequency (how often an organization successfully releases to production)"""
    if not prs:
        return None
        
    # Count deployments per day
    deployments_by_date = defaultdict(int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    for pr in prs:
        if pr.get("merged_at"):  # Consider merged PRs as deployments
            merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            if start_date <= merged_date <= end_date:
                date_key = merged_date.date()
                deployments_by_date[date_key] += 1
    
    if not deployments_by_date:
        return 0
        
    # Calculate average deployments per day
    total_deployments = sum(deployments_by_date.values())
    return total_deployments / days

def calculate_mttr(prs):
    """Calculate Mean Time to Recovery (how long it takes to fix a failed deployment)"""
    if not prs:
        return None
        
    recovery_times = []
    for pr in prs:
        # Look for PRs that are marked as fixes or reverts
        title = pr.get("title", "").lower()
        if any(keyword in title for keyword in ["fix", "hotfix", "revert", "rollback"]):
            if pr.get("merged_at") and pr.get("created_at"):
                created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                recovery_times.append((merged - created).total_seconds() / 3600)  # in hours
    
    if recovery_times:
        return sum(recovery_times) / len(recovery_times)
    return None

def calculate_change_failure_rate(prs):
    """Calculate Change Failure Rate (percentage of deployments causing a failure in production)"""
    if not prs:
        return None
        
    total_deployments = 0
    failed_deployments = 0
    
    for pr in prs:
        if pr.get("merged_at"):  # Count only merged PRs
            total_deployments += 1
            # Look for indicators of failures in PR title or body
            title = pr.get("title", "").lower()
            body = pr.get("body", "").lower()
            
            if any(keyword in title or keyword in body 
                  for keyword in ["fix", "hotfix", "revert", "rollback", "emergency"]):
                failed_deployments += 1
    
    if total_deployments > 0:
        return (failed_deployments / total_deployments) * 100  # Return as percentage
    return None
