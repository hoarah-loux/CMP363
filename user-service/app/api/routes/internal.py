from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import provide_session
from app.services.user_service import crud_user
from app.schemas.user import UserResponse

internal_router = APIRouter(prefix="/users", tags=["Internal"])


@internal_router.get("/{user_id}/", response_model=UserResponse)
async def internal_get_user(user_id: int, session: AsyncSession = Depends(provide_session)):
    # Public internal lookup used by other services (no auth)
    user = await crud_user.get(session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
