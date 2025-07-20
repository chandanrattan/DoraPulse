from fastapi import FastAPI, HTTPException, Depends, status
from common.github_client import GitHubClient
from metrics.dora_metrics import (
    calculate_lead_time,
    calculate_deployment_frequency,
    calculate_mttr,
    calculate_change_failure_rate
)
from metrics.export_to_excel import save_dora_metrics_to_excel
from fastapi.middleware.cors import CORSMiddleware
from auth.auth import verify_token, api_key_header

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/metrics/generate")
async def generate_metrics(token: str = Depends(api_key_header), repo: str = None):
    try:
        # Extract token from the Authorization header
        if not token.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid token format. Token must start with 'Bearer '"
            )
        github_token = token.split("Bearer ")[1]
        
        # Get repo from query parameter
        if not repo:
            raise HTTPException(status_code=400, detail="Repository name is required")
            
        # Create a GitHub client with the token and repo from frontend
        github_client = GitHubClient(github_token, repo)
        
        # Validate the token first
        await github_client.validate_credentials()
        
        # Fetch and process pull requests
        print(f"Fetching pull requests for repository: {repo}")
        prs = await github_client.fetch_pull_requests()
        print(f"Found {len(prs) if prs else 0} pull requests")
        
        if not prs:
            print("No pull requests found, returning zero metrics")
            return {
                "Deployment Frequency": 0,
                "Lead Time (hrs)": 0,
                "MTTR (hrs)": 0,
                "Change Failure Rate": 0
            }

        # Calculate metrics
        deployment_freq = calculate_deployment_frequency(prs)
        lead_time = calculate_lead_time(prs)
        mttr = calculate_mttr(prs)
        failure_rate = calculate_change_failure_rate(prs)
        
        print("Calculated metrics:")
        print(f"- Deployment Frequency: {deployment_freq}")
        print(f"- Lead Time: {lead_time} hrs")
        print(f"- MTTR: {mttr} hrs")
        print(f"- Change Failure Rate: {failure_rate}")
        
        result = {
            "Deployment Frequency": deployment_freq,
            "Lead Time (hrs)": lead_time,
            "MTTR (hrs)": mttr,
            "Change Failure Rate": failure_rate
        }
        
        # Convert None values to 0
        result = {k: v if v is not None else 0 for k, v in result.items()}
        
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error generating metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate metrics: {str(e)}"
        )
