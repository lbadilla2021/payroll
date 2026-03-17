from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str = 'postgresql+psycopg2://payroll:payroll@db:5432/payroll'
    jwt_secret: str = 'change-me'
    jwt_algorithm: str = 'HS256'

    access_token_minutes: int = 10
    refresh_token_days: int = 7
    session_idle_timeout_minutes: int = 30
    session_absolute_timeout_days: int = 7
    password_reset_token_minutes: int = 15

    login_max_attempts: int = 5
    login_window_minutes: int = 15
    password_reset_requests_per_hour: int = 5

    password_min_length: int = 12
    blocklist_path: str = 'backend/app/security/password_blocklist.txt'
    allow_global_email_uniqueness: bool = False

    smtp_host: str = 'localhost'
    smtp_port: int = 1025
    smtp_username: str = ''
    smtp_password: str = ''
    smtp_from: str = 'no-reply@payroll.local'
    smtp_from_name: str = 'Payroll Security'
    smtp_use_tls: bool = False
    app_base_url: str = 'http://localhost:8080'

    cookie_secure: bool = False
    cookie_samesite: str = 'lax'
    cookie_domain: str | None = None

    cors_allowed_origins: str = 'http://localhost:8080'

    superadmin_email: str = 'superadmin@payroll.local'
    superadmin_password: str = 'admin123'

    @field_validator('cookie_samesite')
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {'lax', 'strict', 'none'}:
            raise ValueError('COOKIE_SAMESITE inválido')
        return normalized


settings = Settings()
