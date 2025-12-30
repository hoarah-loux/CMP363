from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import provide_session, verify_user
from app.schemas.user import AuthToken
from app.core.security import generate_token

auth_router = APIRouter(tags=["Auth"]) 


@auth_router.post("/login/", response_model=AuthToken)
async def login_user(
    credentials: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(provide_session),
):
    user = await verify_user(session, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    token = generate_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
