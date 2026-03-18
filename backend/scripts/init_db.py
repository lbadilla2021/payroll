from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User
from app.security import hash_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_superadmin() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        raw_email = settings.superadmin_email.strip()
        normalized_email = normalize_email(raw_email)

        if not settings.superadmin_password:
            raise RuntimeError('SUPERADMIN_PASSWORD no configurada')

        existing = db.execute(select(User).where(User.email_normalized == normalized_email)).scalar_one_or_none()
        if existing:
            print('✔ Superadmin ya existe')
            return

        user = User(
            tenant_id=None,
            email_normalized=normalized_email,
            full_name='Super Admin',
            password_hash=hash_password(settings.superadmin_password),
            is_active=True,
            is_superadmin=True,
            is_tenant_admin=False,
            auth_version=1,
        )
        db.add(user)
        db.commit()
        print('✔ Superadmin creado correctamente')
    except Exception as exc:
        db.rollback()
        print(f'❌ Error creando superadmin: {exc}')
        raise
    finally:
        db.close()


if __name__ == '__main__':
    ensure_superadmin()
