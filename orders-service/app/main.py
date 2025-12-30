from fastapi import FastAPI

from app.api.routes.orders import orders_router
from app.db.init_db import init_db
from app.events.consumer import run_consumer
import asyncio


def create_app() -> FastAPI:
    app = FastAPI(title="orders-service")
    app.include_router(orders_router, prefix="/api/v1")

    app.state._consumer_task = None

    @app.on_event("startup")
    async def on_startup() -> None:
        # Create tables on startup (development convenience)
        await init_db()
        # Start background consumer if configured
        try:
            app.state._consumer_task = asyncio.create_task(run_consumer())
        except Exception:
            # best-effort: do not fail startup if RabbitMQ is not available
            app.state._consumer_task = None

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
