from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import provide_session
from app.schemas.order import OrderCreateSchema, OrderResponse
from app.services.order_service import crud_order
from app.services.user_client import get_user, safe_get_user
from app.services.user_snapshot_service import get_snapshot
import asyncio


orders_router = APIRouter(prefix="/orders", tags=["Orders"])


@orders_router.get("/health", status_code=204)
async def health() -> None:
    return None


@orders_router.post("/", response_model=OrderResponse)
async def create_order(order_in: OrderCreateSchema, session: AsyncSession = Depends(provide_session)):
    # Validate owner exists in user-service
    owner = await get_user(order_in.owner_id)
    new_order = await crud_order.create(session, order_in)
    # return with owner info
    return {
        "id": new_order.id,
        "item_name": new_order.item_name,
        "quantity": new_order.quantity,
        "owner_id": new_order.owner_id,
        "owner": {"id": owner.get("id"), "email": owner.get("email"), "full_name": owner.get("full_name")},
    }


@orders_router.get("/", response_model=List[OrderResponse])
async def list_orders(offset: int = 0, limit: int = 100, session: AsyncSession = Depends(provide_session)):
    orders = await crud_order.get_all(session, offset=offset, limit=limit)
    # Enrich orders with owner data when available. Failures to fetch owner do NOT fail the request.
    async def enrich(o):
        owner = await get_snapshot(session, o.owner_id)
        if not owner:
            owner = await safe_get_user(o.owner_id)
        return {
            "id": o.id,
            "item_name": o.item_name,
            "quantity": o.quantity,
            "owner_id": o.owner_id,
            "owner": {"id": owner.get("id"), "email": owner.get("email"), "full_name": owner.get("full_name")} if owner else None,
        }

    enriched = await asyncio.gather(*(enrich(o) for o in orders))
    return enriched


@orders_router.get("/{order_id}/", response_model=OrderResponse)
async def get_order(order_id: int, session: AsyncSession = Depends(provide_session)):
    order = await crud_order.get(session, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    owner = await safe_get_user(order.owner_id)
    return {
        "id": order.id,
        "item_name": order.item_name,
        "quantity": order.quantity,
        "owner_id": order.owner_id,
        "owner": {"id": owner.get("id"), "email": owner.get("email"), "full_name": owner.get("full_name")} if owner else None,
    }
