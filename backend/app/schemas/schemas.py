"""
Pydantic v2 schemas.
Strict separation between request (input) and response (output) schemas
prevents accidental data leakage (e.g., returning password_hash).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

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
    tenant_id: Optional[UUID] = None


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


# ── Invitations ───────────────────────────────────────────────────────────────

class InvitationCreate(BaseModel):
    invited_email: EmailStr
    invited_role: str = Field("viewer", pattern=r"^(superadmin|admin|viewer)$")
    tenant_id: Optional[UUID] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name:  Optional[str] = Field(None, max_length=100)
    job_title:  Optional[str] = Field(None, max_length=150)


class InvitationAccept(BaseModel):
    token: str
    first_name: str  = Field(..., min_length=1, max_length=100)
    last_name:  str  = Field(..., min_length=1, max_length=100)
    password:   str  = Field(..., min_length=10)


class InvitationResponse(BaseModel):
    id: UUID
    invited_email: str
    invited_role: str
    tenant_id: Optional[UUID]
    first_name: Optional[str]
    last_name:  Optional[str]
    job_title:  Optional[str]
    is_accepted: bool
    is_revoked: bool
    expires_at: datetime
    accepted_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    total: int
    page: int
    size: int

# ── RBAC: Permissions ─────────────────────────────────────────────────────────

class PermissionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    module: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionListResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
    page: int
    size: int


# ── RBAC: Tenant Roles ────────────────────────────────────────────────────────

class TenantRoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: list[UUID] = Field(default_factory=list)


class TenantRoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class TenantRolePermissionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    module: str

    model_config = ConfigDict(from_attributes=True)


class TenantRoleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: list[TenantRolePermissionResponse] = Field(default_factory=list)
    user_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TenantRoleListResponse(BaseModel):
    items: list[TenantRoleResponse]
    total: int
    page: int
    size: int


# ── RBAC: Role permission assignment ─────────────────────────────────────────

class RolePermissionsSet(BaseModel):
    """Replace the full set of permissions for a role."""
    permission_ids: list[UUID]


# ── RBAC: User role assignment ────────────────────────────────────────────────

class UserRoleAssign(BaseModel):
    user_id: UUID
    tenant_role_ids: list[UUID] = Field(..., min_length=1)


class UserTenantRoleResponse(BaseModel):
    user_id: UUID
    tenant_role_id: UUID
    assigned_at: datetime
    role_name: str
    role_is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserRolesResponse(BaseModel):
    user_id: UUID
    roles: list[UserTenantRoleResponse]
