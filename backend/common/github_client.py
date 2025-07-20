import os
from typing import Optional, List, Dict, Any
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class GitHubClient:
    def __init__(self, token: str, repo: str):
        self.github_token = token
        self.github_repo = repo
        self.api_url = "https://api.github.com"
        
        if not self.github_token:
            raise ValueError("GitHub token is required")
        if not self.github_repo:
            raise ValueError("GitHub repository is required")
        
        print("GitHub Client initialized with:")
        print(f"Repository: {self.github_repo}")
        print(f"Token: {'Present' if self.github_token else 'Missing'}")
            
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        
    async def validate_credentials(self) -> bool:
        """Validate GitHub credentials by making a test API call"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/repos/{self.github_repo}",
                    headers=self.headers
                )
                response.raise_for_status()
                return True
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid GitHub token")
                elif e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Repository not found")
                else:
                    raise HTTPException(status_code=e.response.status_code, detail=str(e))
                
    async def fetch_pull_requests(
        self, 
        state: str = "closed", 
        start_date: Optional[datetime] = None
    ) -> List[Dict[Any, Any]]:
        """
        Fetch pull requests from GitHub with pagination and date filtering
        
        Args:
            state: PR state to fetch (open, closed, all)
            start_date: Optional start date to filter PRs
            
        Returns:
            List of pull request data
        """
        url = f"{self.api_url}/repos/{self.github_repo}/pulls"
        params = {"state": state, "per_page": 100, "page": 1}
        all_pulls = []
        
        if start_date:
            params["since"] = start_date.isoformat()

        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    pulls = response.json()
                    print(f"Fetched {len(pulls)} pull requests")
                    if not pulls:
                        break
                        
                    all_pulls.extend(pulls)
                    
                    # Check if we've reached the last page
                    if len(pulls) < 100:
                        break
                        
                    params["page"] += 1
                    
                except httpx.HTTPStatusError as e:
                    raise HTTPException(
                        status_code=e.response.status_code,
                        detail=f"GitHub API error: {str(e)}"
                    )
                except httpx.RequestError as e:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Failed to connect to GitHub: {str(e)}"
                    )

        return all_pulls
