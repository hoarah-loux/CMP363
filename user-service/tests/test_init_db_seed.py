import asyncio
import pathlib
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import pytest

# Ensure tests can import the local `app` package by adding the service dir to sys.path
service_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(service_dir))

# Provide a lightweight shim for 'jose' if it's not installed so tests can import modules that reference it
if "jose" not in sys.modules:
    import types

    jwt_mod = types.SimpleNamespace(encode=lambda *a, **k: "", decode=lambda *a, **k: {}, JWTError=Exception)
    shim = types.SimpleNamespace(jwt=jwt_mod, JWTError=Exception)
    sys.modules["jose"] = shim

from app.core.config import settings
from app.db.init_db import init_db
from app.models.user import User
from app.core.security import verify_password


def test_init_db_seeds_admin(monkeypatch, tmp_path):
    """Run the async init flow using asyncio.run so pytest doesn't require pytest-asyncio."""
    try:
        async def runner():
            # Use a file-backed sqlite DB in tmp_path so table state is visible across connections
            db_path = tmp_path / "user_test.db"
            monkeypatch.setattr(settings, "POSTGRES_URI", f"sqlite+aiosqlite:///{db_path}")
            monkeypatch.setattr(settings, "FIRST_USER_EMAIL", "seed-admin@example.com")
            monkeypatch.setattr(settings, "FIRST_USER_PASSWORD", "seed_pass")

            # Run init_db (creates tables and seeds admin)
            await init_db()

            # Connect and verify
            engine = create_async_engine(settings.POSTGRES_URI)
            SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

            async with SessionLocal() as session:
                result = await session.execute(User.__table__.select().where(User.email == settings.FIRST_USER_EMAIL))
                row = result.first()
                assert row is not None
                # row is a RowMapping; construct a simple check
                user_id = row[0]
                # load the user object
                user = await session.get(User, user_id)
                assert user.email == settings.FIRST_USER_EMAIL
                assert user.is_superuser is True
                assert verify_password(settings.FIRST_USER_PASSWORD, user.hashed_password)

        asyncio.run(runner())
    finally:
        # cleanup sys.path to avoid interference with other tests
        try:
            sys.path.remove(str(service_dir))
        except ValueError:
            pass
