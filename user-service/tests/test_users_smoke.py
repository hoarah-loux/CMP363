import pathlib
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _load_app_from_service(service_root: pathlib.Path):
    """Helper: temporarily add service root to sys.path and import app.main"""
    import sys as _sys
    _sys.path.insert(0, str(service_root))
    try:
        # Provide minimal jose shim for imports if not installed
        if "jose" not in _sys.modules:
            import types

            jwt_mod = types.SimpleNamespace(decode=lambda *a, **k: {})
            shim = types.SimpleNamespace(jwt=jwt_mod, JWTError=Exception)
            _sys.modules["jose"] = shim

        import importlib
        # Clear any previously loaded 'app' modules to ensure we import the correct service package
        for modname in list(_sys.modules.keys()):
            if modname == "app" or modname.startswith("app."):
                del _sys.modules[modname]
        mod = importlib.import_module("app.main")
        return mod.app
    finally:
        _sys.path.remove(str(service_root))


@pytest.fixture(autouse=True)
def disable_startup():
    # Prevent DB init on import/startup during tests
    service_root = pathlib.Path(__file__).resolve().parent.parent
    app = _load_app_from_service(service_root)
    app.router.on_startup.clear()
    return


def test_health_endpoint():
    service_root = pathlib.Path(__file__).resolve().parent.parent
    app = _load_app_from_service(service_root)
    client = TestClient(app)
    r = client.get("/api/v1/users/health")
    assert r.status_code == 204


def test_login_success():
    service_root = pathlib.Path(__file__).resolve().parent.parent
    app = _load_app_from_service(service_root)
    client = TestClient(app)

    # Create a fake user object
    class FakeUser:
        def __init__(self):
            self.id = 1
            self.is_active = True

    fake_user = FakeUser()

    # Patch verify_user on the imported app package to ensure the running app uses the mock
    import importlib
    # Patch the objects that the auth route actually references (auth module imports verify_user at import time)
    auth_mod = importlib.import_module("app.api.routes.auth")
    # Patch the objects that the auth route actually references (it imported generate_token at import time)
    with patch.object(auth_mod, "verify_user", AsyncMock(return_value=fake_user)), \
         patch.object(auth_mod, "generate_token", return_value="mock-token"):
        resp = client.post(
            "/api/v1/login/",
            data={"username": "test@example.com", "password": "test_pass"},
        )

    assert resp.status_code == 200
    assert resp.json()["access_token"] == "mock-token"
