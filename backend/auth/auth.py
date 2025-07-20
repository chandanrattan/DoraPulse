from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

# Use API Key auth instead of OAuth2
api_key_header = APIKeyHeader(name="Authorization")

async def verify_token(token: str = None) -> Optional[str]:
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format. Use 'Bearer YOUR_GITHUB_TOKEN'"
        )
    return token.split(" ")[1]  # Return just the token part
