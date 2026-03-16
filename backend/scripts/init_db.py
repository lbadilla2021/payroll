from pathlib import Path
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import engine, SessionLocal
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


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []

    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current.append(line)
        if stripped.endswith(';'):
            statement = '\n'.join(current).strip().rstrip(';').strip()
            if statement:
                statements.append(statement)
            current = []

    if current:
        statement = '\n'.join(current).strip().rstrip(';').strip()
        if statement:
            statements.append(statement)

    return statements


def run_migrations() -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / 'migrations'
    with engine.begin() as conn:
        for migration_file in sorted(migrations_dir.glob('*.sql')):
            sql = migration_file.read_text(encoding='utf-8')
            for statement in _split_sql_statements(sql):
                conn.execute(text(statement))


def ensure_superadmin() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.superadmin_email).first()
        if existing:
            try:
                password_matches = verify_password(settings.superadmin_password, existing.password_hash)
            except Exception:
                password_matches = False

            needs_update = (
                not password_matches
                or existing.role != 'superadmin'
                or existing.tenant_id is not None
                or not existing.is_active
            )
            if needs_update:
                existing.full_name = 'Super Admin'
                existing.password_hash = hash_password(settings.superadmin_password)
                existing.role = 'superadmin'
                existing.tenant_id = None
                existing.is_active = True
                db.commit()
            return

        user = User(
            email=settings.superadmin_email,
            full_name='Super Admin',
            password_hash=hash_password(settings.superadmin_password),
            role='superadmin',
            tenant_id=None,
            is_active=True,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    wait_for_db()
    run_migrations()
    ensure_superadmin()
    print('Database initialized.')
