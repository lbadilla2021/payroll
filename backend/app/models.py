from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    users = relationship('User', back_populates='tenant')
    sessions = relationship('UserSession', back_populates='tenant')
    password_reset_tokens = relationship('PasswordResetToken', back_populates='tenant')
    audit_logs = relationship('AuthAuditLog', back_populates='tenant')


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
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    tenant = relationship('Tenant', back_populates='users')
    sessions = relationship('UserSession', back_populates='user')
    password_reset_tokens = relationship('PasswordResetToken', back_populates='user')
    audit_logs = relationship('AuthAuditLog', back_populates='user')

    __table_args__ = (
        UniqueConstraint('tenant_id', 'email_normalized', name='uq_users_tenant_email_normalized'),
        Index('ix_users_email_normalized', 'email_normalized'),
    )


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(String(64), primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    refresh_token_hash = Column(String(128), nullable=False, index=True)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    idle_expires_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(String(128), nullable=True)
    rotated_from_session_id = Column(String(64), nullable=True)

    user = relationship('User', back_populates='sessions')
    tenant = relationship('Tenant', back_populates='sessions')


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    requested_ip = Column(String(64), nullable=True)
    requested_user_agent = Column(String(512), nullable=True)

    tenant = relationship('Tenant', back_populates='password_reset_tokens')
    user = relationship('User', back_populates='password_reset_tokens')


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
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    tenant = relationship('Tenant', back_populates='audit_logs')
    user = relationship('User', back_populates='audit_logs')


class AuthRateLimitBucket(Base):
    __tablename__ = 'auth_rate_limit_buckets'

    key = Column(String(255), primary_key=True)
    count = Column(Integer, nullable=False, default=0)
    window_started_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
