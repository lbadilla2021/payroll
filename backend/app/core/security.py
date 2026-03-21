"""
Security layer: password hashing, JWT generation/validation, CSRF tokens.

Strategy chosen: httpOnly cookie-based session with dual tokens.
- Access token (30 min, httpOnly, Secure, SameSite=Lax) → rides every request
- Refresh token (7 days, httpOnly, Secure, SameSite=Strict, path=/api/v1/auth/refresh)
- CSRF double-submit cookie pattern for mutation endpoints

Rationale:
  - httpOnly cookies: XSS cannot read tokens (superior to localStorage)
  - Short-lived access token: blast radius of theft is small
  - Refresh token path-scoped: only sent to refresh endpoint
  - SameSite=Lax on access: CSRF protection for navigational requests
  - CSRF header required for mutations: defense in depth against CSRF
  - No token blacklist needed for access tokens (short TTL)
  - Refresh tokens stored hashed in DB for revocation on logout/pwd change
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
# bcrypt with cost 12 — balances security and performance
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    tenant_id: Optional[str] = None,
    role: Optional[str] = None,
    extra_claims: dict = {},
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "tid": tenant_id,
        "role": role,
        **extra_claims,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_urlsafe(32),  # unique ID for revocation
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises JWTError on failure. Caller must handle."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ── Secure random tokens ──────────────────────────────────────────────────────

def generate_secure_token(nbytes: int = 32) -> str:
    """URL-safe token suitable for password reset links."""
    return secrets.token_urlsafe(nbytes)


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


# ── Password policy ───────────────────────────────────────────────────────────

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Minimum {settings.PASSWORD_MIN_LENGTH} characters required."
    if not any(c.isupper() for c in password):
        return False, "Must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Must contain at least one digit."
    special = set(string.punctuation)
    if not any(c in special for c in password):
        return False, "Must contain at least one special character."
    return True, ""
