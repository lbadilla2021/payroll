import re
from typing import Optional

from pydantic import BaseModel, field_validator


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise ValueError('Email inválido')
    return email


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return _normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserInfo(BaseModel):
    id: int
    email: str
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
    email: str
    full_name: str
    password: str
    role: str
    tenant_id: Optional[int] = None

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return _normalize_email(value)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    tenant_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True
