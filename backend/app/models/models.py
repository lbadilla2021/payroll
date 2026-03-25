"""
SQLAlchemy ORM models.

Multi-tenant strategy: SHARED database, SHARED schema with tenant_id discriminator
on every tenant-scoped table. Row-Level Security is enforced at the application
layer via mandatory tenant_id filtering in all repository queries.

Chosen over:
  - Separate DB per tenant: overkill at this stage, ops complexity high
  - Separate schema per tenant: complex migrations, Django-style but fragile

This approach scales to hundreds of tenants and can be migrated to schema-per-tenant
later if needed via a data migration with zero model changes.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, func,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


# ── Tenants ───────────────────────────────────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    max_users = Column(Integer, nullable=False, default=5)
    plan = Column(String(50), nullable=False, default="basic")  # basic|pro|enterprise

    # Contact / Legal
    contact_email = Column(String(254), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    legal_name = Column(String(300), nullable=True)
    tax_id = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="dynamic")
    tenant_roles = relationship("TenantRole", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tenants_is_active", "is_active"),
    )


# ── Users ─────────────────────────────────────────────────────────────────────

class UserRole(str):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    VIEWER = "viewer"  # extensible


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True)
    # superadmin has tenant_id=NULL; all other roles require tenant_id

    email = Column(String(254), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")

    is_active = Column(Boolean, nullable=False, default=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    force_password_change = Column(Boolean, nullable=False, default=False)

    phone = Column(String(30), nullable=True)
    job_title = Column(String(150), nullable=True)

    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    user_tenant_roles = relationship("UserTenantRole", foreign_keys="UserTenantRole.user_id", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_tenant_id", "tenant_id"),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"


# ── Refresh Tokens ────────────────────────────────────────────────────────────

class RefreshToken(Base):
    """
    Stored hashed refresh tokens allow server-side revocation:
    - on logout
    - on password change
    - on account deactivation
    Without this, JWTs are stateless and cannot be revoked before expiry.
    """
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)  # SHA-256 of raw token
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, nullable=False, default=False)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash"),
    )


# ── Password Reset Tokens ─────────────────────────────────────────────────────

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)

    user = relationship("User", back_populates="password_reset_tokens")

    __table_args__ = (
        Index("ix_prt_user_id", "user_id"),
        Index("ix_prt_token_hash", "token_hash"),
    )


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable audit trail. Never updated or deleted.
    Structured for future SIEM integration.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)       # null for platform events
    user_id = Column(UUID(as_uuid=True), nullable=True)          # null for anonymous events
    actor_email = Column(String(254), nullable=True)
    action = Column(String(100), nullable=False)                  # e.g. "user.login"
    resource_type = Column(String(100), nullable=True)            # e.g. "user"
    resource_id = Column(String(100), nullable=True)
    outcome = Column(String(20), nullable=False, default="success")  # success|failure|error
    detail = Column(Text, nullable=True)                           # JSON-serialized context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_tenant_id", "tenant_id"),
        Index("ix_audit_user_id", "user_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_created_at", "created_at"),
    )


# ── Invitation Tokens ─────────────────────────────────────────────────────────

class InvitationToken(Base):
    """
    Pending invitations sent by admins/superadmins.
    The invited person receives an email with a signed link.
    On acceptance, the user account is created with their own password.
    Token is single-use and expires after TTL (default 72h).
    """
    __tablename__ = "invitation_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    invited_email = Column(String(254), nullable=False, index=True)
    invited_role = Column(String(50), nullable=False, default="viewer")
    token_hash = Column(String(255), nullable=False, unique=True)  # SHA-256 of raw token

    first_name = Column(String(100), nullable=True)   # optional pre-fill
    last_name  = Column(String(100), nullable=True)
    job_title  = Column(String(150), nullable=True)

    expires_at  = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    is_accepted = Column(Boolean, nullable=False, default=False)
    is_revoked  = Column(Boolean, nullable=False, default=False)

    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant     = relationship("Tenant")
    invited_by = relationship("User", foreign_keys=[invited_by_id])

    __table_args__ = (
        Index("ix_invitation_tokens_tenant_id",    "tenant_id"),
        Index("ix_invitation_tokens_token_hash",   "token_hash"),
        Index("ix_invitation_tokens_invited_email","invited_email"),
    )


# ── RBAC: Permission Catalog ──────────────────────────────────────────────────

class Permission(Base):
    """
    Global catalog of all available permissions in the platform.
    Future modules INSERT their own permissions here on initialization.
    Format: 'module.resource.action' e.g. 'platform.users.create'
    """
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    role_permissions = relationship("TenantRolePermission", back_populates="permission", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_permissions_module", "module"),
        Index("ix_permissions_is_active", "is_active"),
    )


# ── RBAC: Tenant Roles ────────────────────────────────────────────────────────

class TenantRole(Base):
    """
    Roles defined by each tenant. Admins manage these for their tenant.
    is_system=True roles are created by the platform and cannot be deleted.
    """
    __tablename__ = "tenant_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_system = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="tenant_roles")
    role_permissions = relationship("TenantRolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserTenantRole", back_populates="tenant_role", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_roles_tenant_name"),
        Index("ix_tenant_roles_tenant_id", "tenant_id"),
        Index("ix_tenant_roles_is_active", "is_active"),
    )


# ── RBAC: Tenant Role Permissions (junction) ──────────────────────────────────

class TenantRolePermission(Base):
    """Which permissions a tenant role has."""
    __tablename__ = "tenant_role_permissions"

    tenant_role_id = Column(UUID(as_uuid=True), ForeignKey("tenant_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id  = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    role = relationship("TenantRole", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        Index("ix_trp_tenant_role_id", "tenant_role_id"),
        Index("ix_trp_permission_id", "permission_id"),
    )


# ── RBAC: User Tenant Roles (junction) ────────────────────────────────────────

class UserTenantRole(Base):
    """Which tenant roles a user has (N:M)."""
    __tablename__ = "user_tenant_roles"

    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tenant_role_id = Column(UUID(as_uuid=True), ForeignKey("tenant_roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="user_tenant_roles")
    tenant_role = relationship("TenantRole", back_populates="user_roles")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])

    __table_args__ = (
        Index("ix_utr_user_id", "user_id"),
        Index("ix_utr_tenant_role_id", "tenant_role_id"),
    )


# ── Groups ────────────────────────────────────────────────────────────────────

class Group(Base):
    """
    Named grouping of users within a tenant.
    Groups can be assigned tenant_roles — all members inherit those permissions.
    """
    __tablename__ = "groups"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active   = Column(Boolean, nullable=False, default=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    tenant      = relationship("Tenant")
    created_by  = relationship("User", foreign_keys=[created_by_id])
    members     = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    group_roles = relationship("GroupRole", back_populates="group", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_groups_tenant_name"),
        Index("ix_groups_tenant_id", "tenant_id"),
        Index("ix_groups_is_active", "is_active"),
    )


class GroupMember(Base):
    """User membership in a group."""
    __tablename__ = "group_members"

    group_id   = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id",  ondelete="CASCADE"), primary_key=True)
    added_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    added_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    group    = relationship("Group", back_populates="members")
    user     = relationship("User", foreign_keys=[user_id])
    added_by = relationship("User", foreign_keys=[added_by_id])

    __table_args__ = (
        Index("ix_group_members_group_id", "group_id"),
        Index("ix_group_members_user_id",  "user_id"),
    )


class GroupRole(Base):
    """Which tenant_roles are assigned to a group."""
    __tablename__ = "group_roles"

    group_id       = Column(UUID(as_uuid=True), ForeignKey("groups.id",       ondelete="CASCADE"), primary_key=True)
    tenant_role_id = Column(UUID(as_uuid=True), ForeignKey("tenant_roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id",        ondelete="SET NULL"), nullable=True)
    assigned_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    group       = relationship("Group", back_populates="group_roles")
    tenant_role = relationship("TenantRole")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])

    __table_args__ = (
        Index("ix_group_roles_group_id",       "group_id"),
        Index("ix_group_roles_tenant_role_id", "tenant_role_id"),
    )
