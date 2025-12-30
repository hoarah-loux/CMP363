from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from app.core.jwt_helper import encode as jwt_encode

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Prefer bcrypt but be tolerant of environments where bcrypt's native bindings
# may be unavailable or provide unexpected attributes (which can raise
# AttributeError inside passlib). In that case, fall back to a pure-Python
# algorithm to avoid crashing the application startup (suitable for dev/test).
try:
    password_manager = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as exc:  # pragma: no cover - runtime resilience
    logger.warning("bcrypt backend unavailable (%s); falling back to pbkdf2_sha256", exc)
    password_manager = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_ALGO = "HS256"


def hash_password(plain: str) -> str:
    return password_manager.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_manager.verify(plain, hashed)


def generate_token(user_id: int, minutes: Optional[int] = None) -> str:
    expiry_minutes = minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "user_id": str(user_id),
        # PyJWT accepts datetime for 'exp', but our fallback expects a numeric timestamp
        "exp": int((datetime.utcnow() + timedelta(minutes=expiry_minutes)).timestamp()),
    }
    return jwt_encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=JWT_ALGO,
    )
