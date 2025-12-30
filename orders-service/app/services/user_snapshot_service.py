from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_snapshot import UserSnapshot


async def upsert_snapshot(session: AsyncSession, *, user_id: int, email: str | None = None, full_name: str | None = None) -> None:
    existing = await session.execute(select(UserSnapshot).where(UserSnapshot.user_id == user_id))
    inst = existing.scalars().first()
    if inst:
        inst.email = email
        inst.full_name = full_name
        session.add(inst)
        await session.commit()
    else:
        inst = UserSnapshot(user_id=user_id, email=email, full_name=full_name)
        session.add(inst)
        await session.commit()


async def get_snapshot(session: AsyncSession, user_id: int) -> Optional[dict]:
    result = await session.execute(select(UserSnapshot).where(UserSnapshot.user_id == user_id))
    inst = result.scalars().first()
    if not inst:
        return None
    return {"id": inst.user_id, "email": inst.email, "full_name": inst.full_name}
