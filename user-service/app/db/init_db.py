from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.core.security import hash_password



async def init_db() -> None:
    """Create database tables from metadata."""
    from app.db.session import engine
    # simple convenience for dev: create tables
    # ensure all models are imported so their tables are registered with metadata
    import app.models.user  # noqa: F401 - register user model
    from app.db.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial superuser if configured and not already present
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with AsyncSessionLocal() as session:
        # Check if a first user is configured
        email = settings.FIRST_USER_EMAIL
        password = settings.FIRST_USER_PASSWORD
        if email and password:
            existing = await session.execute(
                # use filter_by for simplicity
                User.__table__.select().where(User.email == email)
            )
            if existing.first() is None:
                # support SecretStr or plain string in tests/environments
                if hasattr(password, "get_secret_value"):
                    raw_pw = password.get_secret_value()
                else:
                    raw_pw = str(password)
                hashed = hash_password(raw_pw)
                # Use core insert to avoid triggering mapper relationship resolution during test imports
                await session.execute(
                    User.__table__.insert().values(full_name="Admin", email=email, hashed_password=hashed, is_active=True, is_superuser=True)
                )
                await session.commit()
