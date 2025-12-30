import pathlib
import pytest

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health():
    # Import inside test to avoid cross-service package conflicts during collection
    service_dir = pathlib.Path(__file__).resolve().parent.parent
    import sys as _sys
    _sys.path.insert(0, str(service_dir))
    try:
        import importlib
        orders_app = importlib.import_module("app.main")
        app = orders_app.app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            r = await ac.get("/api/v1/orders/health")
        assert r.status_code == 204
    finally:
        _sys.path.remove(str(service_dir))
