from typing import Optional

from pydantic import BaseModel


class OrderCreateSchema(BaseModel):
    item_name: str
    quantity: int = 1
    owner_id: int


class OrderResponse(BaseModel):
    id: int
    item_name: str
    quantity: int
    owner_id: int
    owner: dict | None = None

    class Config:
        from_attributes = True
