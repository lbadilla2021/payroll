import re
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from app.config import settings

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise ValueError('Email inválido')
    return email


class LoginRequest(BaseModel):
    tenant_code: Optional[str] = None
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return _normalize_email(value)


class ForgotPasswordRequest(BaseModel):
    tenant_code: Optional[str] = None
    email: str

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return _normalize_email(value)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    new_password_confirm: str

    @model_validator(mode='after')
    def check_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError('Las contraseñas no coinciden')
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str

    @model_validator(mode='after')
    def check_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError('Las contraseñas no coinciden')
        return self


class LogoutRequest(BaseModel):
    all_sessions: bool = False


class GenericMessage(BaseModel):
    message: str


class UserInfo(BaseModel):
    id: int
    tenant_id: Optional[int]
    email_normalized: str
    full_name: str
    is_superadmin: bool
    is_tenant_admin: bool

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserInfo
    expires_in_seconds: int = settings.access_token_minutes * 60


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
    tenant_id: int

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return _normalize_email(value)


class UserOut(BaseModel):
    id: int
    tenant_id: Optional[int]
    email_normalized: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    is_tenant_admin: bool

    class Config:
        from_attributes = True
