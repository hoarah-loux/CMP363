import asyncio
import pathlib

from httpx import AsyncClient


def test_users_health_and_internal_notfound():
    async def _inner():
        # Import inside test to avoid cross-service package conflicts during collection
        service_dir = pathlib.Path(__file__).resolve().parent.parent
        import sys as _sys
        _sys.path.insert(0, str(service_dir))
        try:
            # Provide minimal jose shim for imports if not installed
            if "jose" not in _sys.modules:
                import types

                jwt_mod = types.SimpleNamespace(decode=lambda *a, **k: {})
                shim = types.SimpleNamespace(jwt=jwt_mod, JWTError=Exception)
                _sys.modules["jose"] = shim

            import importlib
            # Remove any existing 'app' packages from sys.modules to avoid cross-service collisions
            for modname in list(_sys.modules.keys()):
                if modname == "app" or modname.startswith("app."):
                    del _sys.modules[modname]
            user_app = importlib.import_module("app.main")
            app = user_app.app
            # Patch the user_service crud to avoid hitting an empty sqlite DB
            svc_mod = importlib.import_module("app.services.user_service")
            from fastapi.testclient import TestClient
            from unittest.mock import AsyncMock, patch as _patch

            with _patch.object(svc_mod.crud_user, "get", AsyncMock(return_value=None)):
                client = TestClient(app)
                r = client.get("/api/v1/users/health")
                assert r.status_code == 204

                r2 = client.get("/api/v1/internal/users/999999/")
                assert r2.status_code == 404
        finally:
            _sys.path.remove(str(service_dir))

    asyncio.run(_inner())
