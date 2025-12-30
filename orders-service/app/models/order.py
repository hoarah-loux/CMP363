from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class Order(Base):
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True, nullable=False)
    quantity = Column(Integer, default=1)
    owner_id = Column(Integer, index=True, nullable=False)  # references user-service user.id
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
        }
