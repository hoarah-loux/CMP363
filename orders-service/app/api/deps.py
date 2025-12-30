from typing import AsyncGenerator

from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession


async def provide_session() -> AsyncGenerator[AsyncSession, None]:
    async for s in get_session():
        yield s
