"""
FastAPI auth dependencies.

All protected endpoints declare one of these as a dependency:
  - get_current_user: any authenticated user
  - require_superadmin: platform-level operations
  - require_admin_or_superadmin: tenant management
  - get_current_active_user + require_tenant_access: tenant-scoped operations
"""

import hashlib
from typing import Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import RefreshToken, Tenant, User


def _get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )
    return token


def _verify_csrf(request: Request, x_csrf_token: Optional[str] = Header(None)):
    """
    Double-submit CSRF pattern.
    The CSRF token is set as a readable (non-httpOnly) cookie on login.
    The frontend reads it and sends it in X-CSRF-Token header on mutations.
    Backend validates header == cookie value.
    Safe methods (GET, HEAD, OPTIONS) are exempt.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    csrf_cookie = request.cookies.get("csrf_token")
    if not csrf_cookie or csrf_cookie != x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
        )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_csrf),
) -> User:
    token = _get_token_from_cookie(request)
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise JWTError()
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Alias — verifies user is active (already done in get_current_user)."""
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if user.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin access required.")
    return user


def require_admin_or_superadmin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def require_tenant_access(
    tenant_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tenant:
    """
    Validates:
    1. Tenant exists and is active
    2. Non-superadmins can only access their own tenant
    Protects against IDOR at the dependency level.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    if not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive.")
    if user.role != "superadmin" and user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return tenant
