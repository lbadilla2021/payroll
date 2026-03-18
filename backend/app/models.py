from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)

    # 🔐 EMAILS (CORREGIDO)
    email = Column(String(255), nullable=False)
    email_normalized = Column(String(255), nullable=False)

    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)
    is_tenant_admin = Column(Boolean, default=False)

    auth_version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "email_normalized",
            name="uq_users_tenant_email_normalized"
        ),
        Index("ix_users_email_normalized", "email_normalized"),
    )