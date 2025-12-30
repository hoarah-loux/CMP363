import asyncio
from typing import Optional

import httpx

from fastapi import HTTPException

from app.core.config import settings


async def get_order(order_id: int) -> dict:
    """Fetch order and raise on errors (used for validation or other immediate needs)."""
    url = f"{settings.ORDERS_SERVICE_URL}/orders/{order_id}/"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=5.0)
    if resp.status_code == 404:
        raise HTTPException(status_code=400, detail="Order not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=503, detail="Orders service unavailable")
    return resp.json()


async def safe_get_order(order_id: int, retries: int = 1, timeout: float = 2.0) -> Optional[dict]:
    """Attempt to fetch order but return None on failure; used where failure should not bring down the request.

    This function retries `retries` times with exponential backoff.
    """
    url = f"{settings.ORDERS_SERVICE_URL}/orders/{order_id}/"
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
