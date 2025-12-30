from typing import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.jwt_helper import decode as jwt_decode, JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.core.security import JWT_ALGO, verify_password
from app.schemas.user import AuthTokenPayload
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import crud_user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


async def provide_session() -> AsyncGenerator[AsyncSession, None]:
    async for s in get_session():
        yield s


def extract_token_data(token: str = Depends(oauth2_scheme)) -> AuthTokenPayload:
    try:
        payload = jwt_decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[JWT_ALGO])
        return AuthTokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(status_code=403, detail="Invalid or expired token")


async def verify_user(session: AsyncSession, email: str, password: str):
    candidate = await crud_user.get(session, email=email)
    if candidate and verify_password(password, candidate.hashed_password):
        return candidate
    return None


async def fetch_current_user(
    token_data: AuthTokenPayload = Depends(extract_token_data),
    session: AsyncSession = Depends(provide_session),
):
    from app.models.user import User

    user = await crud_user.get(session, id=int(token_data.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def require_superuser(current_user=Depends(fetch_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="User does not have superuser privileges")
    return current_user


on_superuser = require_superuser
