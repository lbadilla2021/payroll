from pathlib import Path
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import SessionLocal, engine
from app.models import User
from app.security import hash_password, verify_password


def wait_for_db(max_retries: int = 30, delay_s: int = 2) -> None:
    for _ in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
                return
        except OperationalError:
            time.sleep(delay_s)
    raise RuntimeError('Database unavailable after retries')


def run_migrations() -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / 'migrations'
    with engine.begin() as conn:
        for migration_file in sorted(migrations_dir.glob('*.sql')):
            sql = migration_file.read_text(encoding='utf-8')
            conn.execute(text(sql))


def ensure_superadmin() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.is_superadmin.is_(True), User.email_normalized == settings.superadmin_email.lower()).first()
        if user:
            valid, _ = verify_password(settings.superadmin_password, user.password_hash)
            if not valid:
                user.password_hash = hash_password(settings.superadmin_password)
            user.is_active = True
            db.commit()
            return

        db.add(
            User(
                tenant_id=None,
                email_normalized=settings.superadmin_email.lower(),
                full_name='Super Admin',
                password_hash=hash_password(settings.superadmin_password),
                is_active=True,
                is_superadmin=True,
                is_tenant_admin=False,
                auth_version=1,
            )
        )
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    wait_for_db()
    run_migrations()
    ensure_superadmin()
    print('Database initialized.')
