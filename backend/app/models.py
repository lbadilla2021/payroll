from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, func
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
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    auth_version = Column(Integer, nullable=False, default=0)
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('superadmin', 'tenant_admin')", name='ck_users_role'),
        CheckConstraint(
            "(role = 'superadmin' AND tenant_id IS NULL) OR (role = 'tenant_admin' AND tenant_id IS NOT NULL)",
            name='ck_users_role_tenant',
        ),
    )

    tenant = relationship('Tenant')


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    refresh_token_hash = Column(String(128), nullable=False)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    absolute_expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(String(128), nullable=True)
    replaced_by_session_id = Column(String(64), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuthAuditLog(Base):
    __tablename__ = 'auth_audit_logs'

    id = Column(Integer, primary_key=True)
    event_type = Column(String(64), nullable=False, index=True)
    outcome = Column(String(32), nullable=False)
    reason = Column(String(255), nullable=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
