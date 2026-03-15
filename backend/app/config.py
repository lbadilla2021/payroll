from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    database_url: str = 'postgresql+psycopg2://payroll:payroll@db:5432/payroll'
    jwt_secret: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    token_expire_minutes: int = 60

    superadmin_email: str = 'superadmin@payroll.local'
    superadmin_password: str = 'admin123'


settings = Settings()
