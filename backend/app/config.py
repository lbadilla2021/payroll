from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str = 'postgresql+psycopg2://payroll:payroll@db:5432/payroll'
    environment: str = 'development'

    jwt_secret: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    jwt_issuer: str = 'payroll-api'
    jwt_audience: str = 'payroll-web'

    access_token_minutes: int = 10
    refresh_token_days: int = 7
    session_idle_timeout_minutes: int = 30
    session_absolute_timeout_minutes: int = 10080
    password_reset_token_minutes: int = 15

    login_max_attempts: int = 5
    login_window_minutes: int = 15
    password_reset_requests_per_hour: int = 5

    cors_allowed_origins: str = 'http://localhost:8080'

    cookie_secure: bool = False
    cookie_samesite: str = 'lax'
    cookie_domain: str | None = None

    app_base_url: str = 'http://localhost:8080'
    enable_password_recovery: bool = True

    smtp_host: str = 'localhost'
    smtp_port: int = 587
    smtp_username: str = 'mailhog'
    smtp_password: str = 'mailhog'
    smtp_from: str = 'no-reply@payroll.local'
    smtp_from_name: str = 'Payroll Security'
    smtp_use_tls: bool = True

    password_min_length: int = 12
    allow_global_email_uniqueness: bool = False
    blocklist_path: str = 'app/security/password_blocklist.txt'

    superadmin_email: str = 'superadmin@payroll.local'
    superadmin_password: str = 'admin123'

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(',') if origin.strip()]

    @property
    def blocklist_file(self) -> Path:
        return Path(self.blocklist_path)

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {'development', 'test', 'staging', 'production'}:
            raise ValueError('ENVIRONMENT inválido')
        return normalized

    @field_validator('cookie_samesite')
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {'lax', 'strict', 'none'}:
            raise ValueError('COOKIE_SAMESITE inválido')
        return normalized

    @field_validator('password_min_length')
    @classmethod
    def validate_password_len(cls, value: int) -> int:
        if value < 10:
            raise ValueError('PASSWORD_MIN_LENGTH debe ser >= 10')
        return value

    @model_validator(mode='after')
    def validate_security_requirements(self):
        weak_jwt_values = {'change-me', 'secret', 'jwt-secret', 'insecure', 'development-secret'}
        if self.environment == 'production':
            if len(self.jwt_secret) < 32 or self.jwt_secret.lower() in weak_jwt_values:
                raise ValueError('JWT_SECRET débil para producción')
            if self.superadmin_password == 'admin123':
                raise ValueError('SUPERADMIN_PASSWORD por defecto no permitido en producción')
            if self.cors_allowed_origins.strip() == '*':
                raise ValueError('CORS_ALLOWED_ORIGINS no puede ser * en producción')
            if self.cookie_samesite == 'none' and not self.cookie_secure:
                raise ValueError('COOKIE_SECURE debe ser true cuando COOKIE_SAMESITE=none en producción')

        if self.enable_password_recovery:
            required = {
                'SMTP_HOST': self.smtp_host.strip(),
                'SMTP_PORT': str(self.smtp_port).strip(),
                'SMTP_USERNAME': self.smtp_username.strip(),
                'SMTP_PASSWORD': self.smtp_password.strip(),
                'SMTP_FROM': self.smtp_from.strip(),
                'SMTP_FROM_NAME': self.smtp_from_name.strip(),
                'APP_BASE_URL': self.app_base_url.strip(),
            }
            missing = [k for k, v in required.items() if not v]
            if missing:
                raise ValueError(f"Faltan variables requeridas para recuperación de contraseña: {', '.join(missing)}")

        return self


settings = Settings()
