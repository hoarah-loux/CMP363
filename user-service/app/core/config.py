from typing import Optional

try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback for test env without pydantic_settings
    try:
        from pydantic import BaseSettings
    except Exception:  # pragma: no cover - if pydantic's BaseSettings is unavailable, provide a minimal shim
        class BaseSettings:  # simple fallback so tests can import the module
            pass

from pydantic import SecretStr, EmailStr, field_validator
from pydantic_core.core_schema import ValidationInfo
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "TestProject"

    POSTGRES_DB: str = "test_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: SecretStr = SecretStr("test_pass")
    POSTGRES_URI: Optional[str] = None

    FIRST_USER_EMAIL: EmailStr = "test@example.com"
    FIRST_USER_PASSWORD: SecretStr = SecretStr("test_pass")
    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"
    RABBITMQ_EXCHANGE: str = "users"

    SECRET_KEY: SecretStr = SecretStr("supersecret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    ORDERS_SERVICE_URL: str = "http://127.0.0.1:8001/api/v1"

    @field_validator("POSTGRES_URI", mode="before")
    @classmethod
    def build_postgres_uri(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        # Respect an explicit POSTGRES_URI environment variable or setting
        if isinstance(v, str) and v:
            return v
        env_uri = os.getenv("POSTGRES_URI")
        if env_uri:
            return env_uri

        # If not explicitly provided via setting or env, return None so
        # the services can fall back to the sqlite dev/test DB without
        # requiring asyncpg to be installed at import time.
        return None


settings = Settings()
