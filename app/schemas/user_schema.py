from pydantic import BaseModel, Field
from typing import Optional

ROLES = {'admin', 'worker'}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: 'UserOut'


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    role: str = 'worker'
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    must_change_password: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


LoginResponse.model_rebuild()
