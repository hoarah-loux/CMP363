from app.db.session import engine


async def init_db() -> None:
    # simple convenience for dev: create tables
    # ensure all models modules are imported so their tables are registered with metadata
    import app.models.order  # noqa: F401 - register order model
    import app.models.user_snapshot  # noqa: F401 - register snapshot model
    from app.db.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
