import asyncio
from typing import Optional

import httpx

from fastapi import HTTPException

from app.core.config import settings


async def get_user(user_id: int) -> dict:
    """Fetch user and raise on errors (used during order create to validate owner exists)."""
    url = f"{settings.USER_SERVICE_URL}/users/{user_id}/"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=5.0)
    if resp.status_code == 404:
        raise HTTPException(status_code=400, detail="Owner user not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=503, detail="User service unavailable")
    return resp.json()


async def safe_get_user(user_id: int, retries: int = 1, timeout: float = 2.0) -> Optional[dict]:
    """Attempt to fetch user but return None on failure; used for enrichment where failure should not bring down the request.

    This function retries `retries` times with exponential backoff.
    """
    url = f"{settings.USER_SERVICE_URL}/users/{user_id}/"
    backoff = 0.5
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return None
        except (httpx.RequestError, httpx.TimeoutException):
            # transient failure – will retry if attempts remain
            if attempt < retries:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            return None
    return None
