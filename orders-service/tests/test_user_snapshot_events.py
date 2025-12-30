import pathlib
import sys
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


def test_process_user_event(tmp_path):
    # make app importable
    service_dir = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(service_dir))
    try:
        import importlib
        cfg = importlib.import_module("app.core.config")
        cfg.settings.POSTGRES_URI = f"sqlite+aiosqlite:///{tmp_path}/orders_events.db"

        # import and create tables
        orders_app = importlib.import_module("app.main")
        from app.db.init_db import init_db

        async def runner():
            await init_db()
            from app.events.consumer import process_user_event
            from app.db.session import _async_session
            from app.services.user_snapshot_service import get_snapshot

            async with _async_session() as session:
                ev = {"type": "user.created", "payload": {"id": 42, "email": "u@example.com", "full_name": "U"}}
                await process_user_event(session, ev)
                snap = await get_snapshot(session, 42)
                assert snap is not None
                assert snap["email"] == "u@example.com"

        asyncio.run(runner())
    finally:
        try:
            sys.path.remove(str(service_dir))
        except ValueError:
            pass
