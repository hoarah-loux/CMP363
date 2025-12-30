from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


# ----------------------------
# Type variables for generics
# ----------------------------
TModel = TypeVar("TModel")
TCreate = TypeVar("TCreate", bound=PydanticBaseModel)
TUpdate = TypeVar("TUpdate", bound=PydanticBaseModel)


# ----------------------------
# Generic CRUD Base
# ----------------------------
class AsyncCRUD(Generic[TModel, TCreate, TUpdate]):
    def __init__(self, model: Type[TModel]) -> None:
        self._model_class = model

    async def create(self, session: AsyncSession, obj_in: TCreate) -> TModel:
        data = obj_in.dict(exclude_unset=True)  # only use fields provided
        instance = self._model_class(**data)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)  # refresh to get auto-generated fields like id
        return instance

    async def get(
        self, session: AsyncSession, *filters, **filter_by
    ) -> Optional[TModel]:
        query = select(self._model_class).filter(*filters).filter_by(**filter_by)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_all(
        self, session: AsyncSession, *filters, offset: int = 0, limit: int = 100, **filter_by
    ) -> List[TModel]:
        query = (
            select(self._model_class)
            .filter(*filters)
            .filter_by(**filter_by)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(query)
        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: Optional[TModel] = None,
        obj_in: Union[TUpdate, Dict[str, Any]],
        **filter_by
    ) -> Optional[TModel]:
        db_obj = db_obj or await self.get(session, **filter_by)
        if db_obj:
            current_data = db_obj.to_dict()
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field in current_data:
                    setattr(db_obj, field, value)
            session.add(db_obj)
            await session.commit()
        return db_obj

    async def delete(
        self, session: AsyncSession, *filters, db_obj: Optional[TModel] = None, **filter_by
    ) -> Optional[TModel]:
        db_obj = db_obj or await self.get(session, *filters, **filter_by)
        if db_obj:
            await session.delete(db_obj)
            await session.commit()
        return db_obj


# ----------------------------
# Order-specific CRUD instance
# ----------------------------
OrderCRUD = AsyncCRUD[Order, PydanticBaseModel, PydanticBaseModel]
crud_order = OrderCRUD(Order)
