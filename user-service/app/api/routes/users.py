from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import provide_session, fetch_current_user, on_superuser
from app.schemas.user import (
    UserCreateSchema,
    UserUpdateDBSchema,
    UserUpdateSchema,
    UserResponse,
)
from app.services.user_service import crud_user
from app.events.publisher import publish_user_event
from app.core.security import hash_password
from app.models.user import User


users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/health")
async def health():
    return {"status": "ok"}



@users_router.get("/", response_model=List[UserResponse], dependencies=[Depends(on_superuser)])
async def read_users(offset: int = 0, limit: int = 100, session: AsyncSession = Depends(provide_session)):
    users = await crud_user.get_all(session, offset=offset, limit=limit)
    return users


@users_router.post("/", response_model=UserResponse, dependencies=[Depends(on_superuser)])
async def create_user(user_in: UserCreateSchema, session: AsyncSession = Depends(provide_session)):
    existing_user = await crud_user.get(session, email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="The user with this email already exists in the system")
    db_obj = UserUpdateDBSchema(**user_in.dict(), hashed_password=hash_password(user_in.password))
    new_user = await crud_user.create(session, db_obj)
    # publish creation event (best-effort)
    try:
        await publish_user_event("created", {"id": new_user.id, "email": new_user.email, "full_name": new_user.full_name, "is_active": new_user.is_active, "is_superuser": new_user.is_superuser})
    except Exception:
        # best-effort: do not fail user creation if publishing fails
        pass
    return new_user


@users_router.get("/{user_id}/", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(fetch_current_user),
    session: AsyncSession = Depends(provide_session),
):
    if current_user.id == user_id:
        return current_user

    user = await crud_user.get(session, id=user_id)
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@users_router.put("/{user_id}/", response_model=UserResponse, dependencies=[Depends(on_superuser)])
async def update_user(
    user_id: int,
    user_in: UserUpdateSchema,
    session: AsyncSession = Depends(provide_session),
):
    user = await crud_user.get(session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="The user with this ID does not exist in the system")
    try:
        update_data = user_in.dict(exclude_unset=True, exclude_none=True)
        if user_in.password:
            update_data["hashed_password"] = hash_password(user_in.password)
        user = await crud_user.update(session, db_obj=user, obj_in=update_data)
        try:
            await publish_user_event("updated", {"id": user.id, "email": user.email, "full_name": user.full_name, "is_active": user.is_active, "is_superuser": user.is_superuser})
        except Exception:
            pass
    except IntegrityError:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    return user


@users_router.delete("/{user_id}/", status_code=204)
async def delete_user(
    user_id: int,
    current_user: User = Depends(on_superuser),
    session: AsyncSession = Depends(provide_session),
):
    user = await crud_user.get(session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == user_id:
        raise HTTPException(status_code=403, detail="User can't delete itself")
    await crud_user.delete(session, db_obj=user)
    try:
        await publish_user_event("deleted", {"id": user.id})
    except Exception:
        pass
