import asyncio

from fastapi import FastAPI

from app.api.routes.users import users_router
from app.api.routes.auth import auth_router
from app.db.init_db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="user-service")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    from app.api.routes.internal import internal_router

    app.include_router(internal_router, prefix="/api/v1/internal")

    @app.on_event("startup")
    async def on_startup() -> None:
        # Create tables on startup (development convenience)
        await init_db()

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
