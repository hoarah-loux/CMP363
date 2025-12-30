import pathlib
from fastapi.testclient import TestClient


def test_orders_health():
    # Import locally to avoid package collisions
    service_dir = pathlib.Path(__file__).resolve().parent.parent
    import sys as _sys
    _sys.path.insert(0, str(service_dir))
    try:
        # Ensure minimal jose shim if jose isn't installed
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
        orders_app = importlib.import_module("app.main")
        app = orders_app.app
        client = TestClient(app)
        r = client.get("/api/v1/orders/health")
        assert r.status_code == 204
    finally:
        _sys.path.remove(str(service_dir))
