"""
Pydantic v2 schemas.
Strict separation between request (input) and response (output) schemas
prevents accidental data leakage (e.g., returning password_hash).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.config import settings
from app.core.security import validate_password_strength


# ── Base / shared ─────────────────────────────────────────────────────────────

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Never includes tokens directly — they ride in cookies."""
    token_type: str = "cookie"
    user: "UserResponse"


class RefreshRequest(BaseModel):
    pass  # refresh token comes from cookie


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        ok, msg = validate_password_strength(self.new_password)
        if not ok:
            raise ValueError(msg)
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        ok, msg = validate_password_strength(self.new_password)
        if not ok:
            raise ValueError(msg)
        return self


# ── Tenant ────────────────────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    max_users: int = Field(default=5, ge=1, le=10000)
    plan: str = Field(default="basic", pattern=r"^(basic|pro|enterprise)$")
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    legal_name: Optional[str] = Field(None, max_length=300)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    plan: Optional[str] = Field(None, pattern=r"^(basic|pro|enterprise)$")
    is_active: Optional[bool] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    legal_name: Optional[str] = Field(None, max_length=300)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None


class TenantResponse(TimestampMixin):
    id: UUID
    name: str
    slug: str
    is_active: bool
    max_users: int
    plan: str
    contact_email: Optional[str]
    contact_phone: Optional[str]
    legal_name: Optional[str]
    tax_id: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    user_count: Optional[int] = None

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    size: int


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: str
    role: str = Field(default="viewer", pattern=r"^(superadmin|admin|viewer)$")
    tenant_id: Optional[UUID] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    job_title: Optional[str] = Field(None, max_length=150)
    force_password_change: bool = False

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, pattern=r"^(superadmin|admin|viewer)$")
    is_active: Optional[bool] = None
    phone: Optional[str] = Field(None, max_length=30)
    job_title: Optional[str] = Field(None, max_length=150)
    force_password_change: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    is_active: bool
    email_verified: bool
    force_password_change: bool
    phone: Optional[str]
    job_title: Optional[str]
    tenant_id: Optional[UUID]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    size: int


# ── Generic ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
