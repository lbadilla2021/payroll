"""
Authentication endpoints.

Cookie strategy:
  - access_token: httpOnly, Secure, SameSite=Lax, Max-Age=ACCESS_TTL
  - refresh_token: httpOnly, Secure, SameSite=Strict, Path=/api/v1/auth/refresh, Max-Age=REFRESH_TTL
  - csrf_token: NOT httpOnly (JS must read), Secure, SameSite=Lax
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rate_limit import login_rate_limit, password_reset_rate_limit
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    generate_secure_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.email.service import send_password_reset_email
from app.models.models import PasswordResetToken, RefreshToken, User
from app.schemas.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit import log_event

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    return xff.split(",")[0].strip() if xff else (request.client.host if request.client else "")


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str):
    is_secure = settings.ENVIRONMENT != "development"
    access_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, secure=is_secure, samesite="lax",
        max_age=access_ttl, path="/",
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=is_secure, samesite="strict",
        max_age=refresh_ttl, path="/api/v1/auth/refresh",
    )
    # csrf_token: readable by JS, not httpOnly
    response.set_cookie(
        key="csrf_token", value=csrf_token,
        httponly=False, secure=is_secure, samesite="lax",
        max_age=access_ttl, path="/",
    )


def _clear_auth_cookies(response: Response):
    for key in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(key=key, path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(login_rate_limit),
):
    ip = _get_ip(request)
    ua = request.headers.get("User-Agent", "")

    # Fetch user — same error for wrong email or wrong password (no enumeration)
    user = db.query(User).filter(User.email == body.email).first()
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )

    if not user or not verify_password(body.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            db.commit()
        log_event(db, "user.login", "failure", actor_email=body.email,
                  detail={"reason": "bad_credentials"}, ip_address=ip)
        raise auth_error

    if not user.is_active:
        log_event(db, "user.login", "failure", user_id=user.id,
                  actor_email=user.email, detail={"reason": "inactive"}, ip_address=ip)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")

    # Validate tenant if user belongs to one
    if user.tenant_id:
        from app.models.models import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not tenant or not tenant.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your organization is inactive.")

    # Reset failed attempts on success
    user.failed_login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = ip

    # Create tokens
    access = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        role=user.role,
    )
    refresh = create_refresh_token(subject=str(user.id))
    csrf = generate_csrf_token()

    # Store hashed refresh token
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=ua,
        ip_address=ip,
    )
    db.add(rt)
    db.commit()

    _set_auth_cookies(response, access, refresh, csrf)
    log_event(db, "user.login", "success", user_id=user.id, actor_email=user.email,
              tenant_id=user.tenant_id, ip_address=ip)

    return TokenResponse(user=UserResponse.model_validate(user))


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Revoke all refresh tokens for this user (logout from all devices)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.is_revoked == False,
    ).update({"is_revoked": True})
    db.commit()

    _clear_auth_cookies(response)
    log_event(db, "user.logout", "success", user_id=user.id, actor_email=user.email)
    return {"message": "Logged out successfully."}


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token.")

    try:
        payload = decode_token(raw_refresh)
        if payload.get("type") != "refresh":
            raise Exception()
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    token_hash = _hash_token(raw_refresh)
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,
    ).first()

    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or invalid.")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

    # Rotate: revoke old, issue new
    stored.is_revoked = True
    new_access = create_access_token(str(user.id), str(user.tenant_id) if user.tenant_id else None, user.role)
    new_refresh = create_refresh_token(str(user.id))
    new_csrf = generate_csrf_token()

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(new_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_rt)
    db.commit()

    _set_auth_cookies(response, new_access, new_refresh, new_csrf)
    return TokenResponse(user=UserResponse.model_validate(user))


# ── Forgot Password ───────────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _: None = Depends(password_reset_rate_limit),
):
    NEUTRAL = {"message": "If that email exists, you will receive a reset link."}
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not user.is_active:
        return NEUTRAL  # Always neutral — no user enumeration

    # Invalidate prior tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False,
    ).update({"is_used": True})

    raw_token = generate_secure_token(48)
    token_hash = _hash_token(raw_token)
    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
        ip_address=_get_ip(request),
    )
    db.add(prt)
    db.commit()

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
    send_password_reset_email(user.email, reset_link, user.first_name)
    log_event(db, "user.password_reset_requested", "success", user_id=user.id, actor_email=user.email)

    return NEUTRAL


# ── Reset Password ────────────────────────────────────────────────────────────

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    token_hash = _hash_token(body.token)
    now = datetime.now(timezone.utc)

    prt = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > now,
    ).first()

    if not prt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link.")

    user = db.query(User).filter(User.id == prt.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset link.")

    user.password_hash = hash_password(body.new_password)
    user.force_password_change = False
    prt.is_used = True
    prt.used_at = now

    # Revoke all sessions (optional but best practice after password reset)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
    _clear_auth_cookies(response)

    db.commit()
    log_event(db, "user.password_reset", "success", user_id=user.id, actor_email=user.email,
              ip_address=_get_ip(request))

    return {"message": "Password reset successfully. Please log in again."}


# ── Change Password (authenticated) ──────────────────────────────────────────

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, user.password_hash):
        log_event(db, "user.password_change", "failure", user_id=user.id,
                  detail={"reason": "wrong_current_password"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

    user.password_hash = hash_password(body.new_password)
    user.force_password_change = False

    # Revoke all refresh tokens → force re-login (best practice)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
    _clear_auth_cookies(response)
    db.commit()

    log_event(db, "user.password_change", "success", user_id=user.id, actor_email=user.email)
    return {"message": "Password changed. Please log in again."}


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
