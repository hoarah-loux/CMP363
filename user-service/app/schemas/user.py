from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, ConfigDict


class AuthToken(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class AuthTokenPayload(BaseModel):
    user_id: Optional[int] = None


class UserCore(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreateSchema(UserCore):
    email: EmailStr
    password: str


class UserDBSchema(UserCore):
    hashed_password: str


class UserResponse(UserCore):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(UserCore):
    password: Optional[str] = None


class UserUpdateDBSchema(UserCore):
    hashed_password: str
