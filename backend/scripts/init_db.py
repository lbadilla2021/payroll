from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.core.config import settings


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_superadmin():
    db = SessionLocal()

    try:
        raw_email = settings.superadmin_email.strip()
        normalized_email = normalize_email(raw_email)

        if not settings.superadmin_password:
            raise RuntimeError("SUPERADMIN_PASSWORD no configurada")

        existing = db.execute(
            select(User).where(User.email_normalized == normalized_email)
        ).scalar_one_or_none()

        if existing:
            print("✔ Superadmin ya existe")
            return

        user = User(
            tenant_id=None,
            email=raw_email,
            email_normalized=normalized_email,
            full_name="Super Admin",
            password_hash=hash_password(settings.superadmin_password),
            is_active=True,
            is_superadmin=True,
            is_tenant_admin=False,
            auth_version=1,
        )

        db.add(user)
        db.commit()

        print("✔ Superadmin creado correctamente")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creando superadmin: {e}")
        raise

    finally:
        db.close()