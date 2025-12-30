from typing import Optional

try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback for test env without pydantic_settings
    try:
        from pydantic import BaseSettings
    except Exception:  # pragma: no cover - if pydantic's BaseSettings is unavailable, provide a minimal shim
        class BaseSettings:  # simple fallback so tests can import the module
            pass

from pydantic import SecretStr, field_validator
from pydantic_core.core_schema import ValidationInfo


class Settings(BaseSettings):
    PROJECT_NAME: str = "OrdersProject"

    POSTGRES_DB: str = "orders_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "orders_user"
    POSTGRES_PASSWORD: SecretStr = SecretStr("orders_pass")
    POSTGRES_URI: Optional[str] = None

    USER_SERVICE_URL: str = "http://10.130.3.129:8000/api/v1/internal"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"
    RABBITMQ_EXCHANGE: str = "users"

    @field_validator("POSTGRES_URI", mode="before")
    @classmethod
    def build_postgres_uri(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        import os
        if isinstance(v, str) and v:
            return v
        env_uri = os.getenv("POSTGRES_URI")
        if env_uri:
            return env_uri

        # If not explicitly provided via setting or env, return None so the
        # services can fall back to the sqlite dev/test DB without requiring
        # asyncpg to be installed at import time.
        return None

        data = info.data
        password: SecretStr = data.get("POSTGRES_PASSWORD", SecretStr(""))
        return (
            f"postgresql+asyncpg://"
            f"{data.get('POSTGRES_USER')}:"
            f"{password.get_secret_value()}@"
            f"{data.get('POSTGRES_HOST')}/"
            f"{data.get('POSTGRES_DB')}"
        )


settings = Settings()
