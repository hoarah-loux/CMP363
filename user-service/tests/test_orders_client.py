import asyncio
import pathlib
from unittest.mock import patch

from fastapi.testclient import TestClient


def _load_app_from_service(service_root: pathlib.Path):
    import sys as _sys
    _sys.path.insert(0, str(service_root))
    try:
        import importlib
        for modname in list(_sys.modules.keys()):
            if modname == "app" or modname.startswith("app."):
                del _sys.modules[modname]
        mod = importlib.import_module("app.main")
        return mod.app
    finally:
        _sys.path.remove(str(service_root))


def test_get_order_and_safe_get(monkeypatch):
    from app.services import orders_client

    # Fake response objects
    class FakeResp:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, resp):
            self.resp = resp

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, timeout=0):
            return self.resp

    # Test get_order success
    monkeypatch.setattr(orders_client.httpx, "AsyncClient", lambda: FakeClient(FakeResp(200, {"id": 1, "item_name": "Widget"})))
    data = asyncio.run(orders_client.get_order(1))
    assert data["item_name"] == "Widget"

    # Test safe_get_order returns None on 404
    monkeypatch.setattr(orders_client.httpx, "AsyncClient", lambda: FakeClient(FakeResp(404)))
    data = asyncio.run(orders_client.safe_get_order(1))
    assert data is None
