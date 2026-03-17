from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    code = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    email_normalized = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superadmin = Column(Boolean, nullable=False, default=False)
    is_tenant_admin = Column(Boolean, nullable=False, default=False)
    auth_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant = relationship('Tenant')

    __table_args__ = (
        UniqueConstraint('tenant_id', 'email_normalized', name='uq_users_tenant_email_normalized'),
        Index('ix_users_email_normalized', 'email_normalized'),
    )


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    refresh_token_hash = Column(String(128), nullable=False, index=True)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    idle_expires_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoke_reason = Column(String(128), nullable=True)
    rotated_from_session_id = Column(String(64), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    requested_ip = Column(String(64), nullable=True)
    requested_user_agent = Column(String(512), nullable=True)


class AuthAuditLog(Base):
    __tablename__ = 'auth_audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    email_input = Column(String(255), nullable=True)
    event_type = Column(String(64), nullable=False, index=True)
    outcome = Column(String(32), nullable=False)
    reason = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class AuthRateLimitBucket(Base):
    __tablename__ = 'auth_rate_limit_buckets'

    key = Column(String(255), primary_key=True)
    count = Column(Integer, nullable=False, default=0)
    window_started_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_auth_rate_limit_updated_at', 'updated_at'),
    )
