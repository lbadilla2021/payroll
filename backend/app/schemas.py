from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserInfo(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    tenant_id: Optional[int]

    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    name: str
    code: str


class TenantOut(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str
    tenant_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    tenant_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True
