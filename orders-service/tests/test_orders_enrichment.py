import pathlib


def test_order_enrichment(tmp_path):
    # Import locally to avoid package collisions
    service_dir = pathlib.Path(__file__).resolve().parent.parent
    import sys as _sys
    _sys.path.insert(0, str(service_dir))
    try:
        import importlib
        # Ensure file-backed sqlite DB so tables are visible across connections used in tests
        cfg = importlib.import_module("app.core.config")
        cfg.settings.POSTGRES_URI = f"sqlite+aiosqlite:///{tmp_path}/orders_test.db"

        # Import the app after we've configured settings

        # Remove any existing 'app' packages from sys.modules to avoid cross-service collisions
        for modname in list(_sys.modules.keys()):
            if modname == "app" or modname.startswith("app."):
                del _sys.modules[modname]

        orders_app = importlib.import_module("app.main")
        app = orders_app.app

        # Ensure DB tables are created before seeding snapshots
        from app.db.init_db import init_db
        import asyncio

        asyncio.run(init_db())
        # smoke-check that the frontend route exists
        from fastapi.testclient import TestClient
        client = TestClient(app)
        r = client.get('/ui/orders')
        assert r.status_code == 200

        # Patch user client functions used by the orders routes to avoid real HTTP calls.
        import importlib
        orders_module = importlib.import_module("app.api.routes.orders")

        fake_user = {"id": 1, "email": "test@example.com", "full_name": "Test User"}

        async def fake_get_user(user_id: int):
            return fake_user

        async def fake_safe_get_user(user_id: int, retries: int = 1, timeout: float = 2.0):
            return fake_user

        # Replace the names used in the routes module (these were imported at module import time)
        orders_module.get_user = fake_get_user
        orders_module.safe_get_user = fake_safe_get_user

        # Ensure there's a user snapshot in DB so enrichment uses it (avoid HTTP calls)
        from app.db.session import _async_session
        from app.events.consumer import process_user_event

        async def seed_snapshot():
            async with _async_session() as session:
                await process_user_event(session, {"type": "user.created", "payload": {"id": 1, "email": "test@example.com", "full_name": "Test User"}})

        import asyncio
        asyncio.run(seed_snapshot())

        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Create an order (create endpoint uses get_user to validate owner)
        r = client.post(
            "/api/v1/orders/",
            json={"item_name": "Widget", "quantity": 3, "owner_id": 1},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["owner"]["email"] == "test@example.com"

        # List orders and ensure enrichment is present
        r = client.get("/api/v1/orders/")
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        assert items[0]["owner"]["email"] == "test@example.com"

    finally:
        _sys.path.remove(str(service_dir))
