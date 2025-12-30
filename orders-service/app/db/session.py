from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
import os

# Use configured POSTGRES_URI when available; fall back to an in-memory sqlite async DB for tests/environments
# If POSTGRES_URI isn't set, ensure aiosqlite is installed so the sqlite fallback works — otherwise fail fast
if not settings.POSTGRES_URI:
    try:
        import aiosqlite  # noqa: F401
    except Exception:
        raise RuntimeError(
            "POSTGRES_URI is not set and 'aiosqlite' is not installed. "
            "Set the POSTGRES_URI env var to a Postgres DSN (e.g. postgresql+asyncpg://user:pass@host/db) "
            "or add 'aiosqlite' to your requirements so the sqlite fallback can run."
        )

DATABASE_URL = settings.POSTGRES_URI or "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
_async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session() as session:
        yield session
