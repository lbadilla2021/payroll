from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, EmailStr, field_validator
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "SaaS Base Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(64)
    API_V1_STR: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Auth / Tokens ─────────────────────────────────────────────────────────
    # httpOnly cookie strategy: access token short-lived, refresh token longer
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    # CSRF token for cookie-based auth
    CSRF_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Password Policy ───────────────────────────────────────────────────────
    PASSWORD_MIN_LENGTH: int = 10
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    LOGIN_RATE_LIMIT: int = 10          # attempts per window
    LOGIN_RATE_WINDOW_SECONDS: int = 300  # 5 min
    PASSWORD_RESET_RATE_LIMIT: int = 3
    PASSWORD_RESET_RATE_WINDOW_SECONDS: int = 3600  # 1 hr

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8080"]

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: EmailStr = "noreply@example.com"
    EMAIL_FROM_NAME: str = "SaaS Platform"

    # ── Frontend URL (for email links) ────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:8080"

    # ── First Superadmin (bootstrap only) ────────────────────────────────────
    FIRST_SUPERADMIN_EMAIL: EmailStr = "admin@platform.com"
    FIRST_SUPERADMIN_PASSWORD: str = "ChangeMe!2024#"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()