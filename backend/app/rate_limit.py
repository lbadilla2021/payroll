from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuthRateLimitBucket


def _now() -> datetime:
    return datetime.now(timezone.utc)


def consume_limit(db: Session, *, key: str, limit: int, window_seconds: int) -> bool:
    now = _now()
    bucket = db.query(AuthRateLimitBucket).filter(AuthRateLimitBucket.key == key).first()
    if not bucket:
        bucket = AuthRateLimitBucket(key=key, count=1, window_started_at=now)
        db.add(bucket)
        return True

    window_start = bucket.window_started_at.replace(tzinfo=timezone.utc)
    if window_start + timedelta(seconds=window_seconds) <= now:
        bucket.count = 1
        bucket.window_started_at = now
        return True

    if bucket.count >= limit:
        return False

    bucket.count += 1
    return True


def check_login_limits(db: Session, *, ip: str, tenant_bucket: str, email: str) -> tuple[bool, str | None]:
    checks = [
        (f'login:ip:{ip}', settings.login_max_attempts * 3, settings.login_window_minutes * 60, 'ip'),
        (f'login:tenant:{tenant_bucket}', settings.login_max_attempts * 10, settings.login_window_minutes * 60, 'tenant'),
        (f'login:acct:{tenant_bucket}:{email.lower()}', settings.login_max_attempts, settings.login_window_minutes * 60, 'email_tenant'),
    ]
    for key, limit, window, dim in checks:
        if not consume_limit(db, key=key, limit=limit, window_seconds=window):
            return False, dim
    return True, None


def check_forgot_limits(db: Session, *, ip: str, tenant_bucket: str, email: str) -> tuple[bool, str | None]:
    checks = [
        (f'forgot:ip:{ip}', settings.password_reset_requests_per_hour * 3, 3600, 'ip'),
        (f'forgot:tenant:{tenant_bucket}', settings.password_reset_requests_per_hour * 10, 3600, 'tenant'),
        (f'forgot:acct:{tenant_bucket}:{email.lower()}', settings.password_reset_requests_per_hour, 3600, 'email_tenant'),
    ]
    for key, limit, window, dim in checks:
        if not consume_limit(db, key=key, limit=limit, window_seconds=window):
            return False, dim
    return True, None


def check_reset_limits(db: Session, *, ip: str, tenant_bucket: str) -> tuple[bool, str | None]:
    checks = [
        (f'reset:ip:{ip}', settings.password_reset_requests_per_hour * 2, 3600, 'ip'),
        (f'reset:tenant:{tenant_bucket}', settings.password_reset_requests_per_hour * 5, 3600, 'tenant'),
    ]
    for key, limit, window, dim in checks:
        if not consume_limit(db, key=key, limit=limit, window_seconds=window):
            return False, dim
    return True, None
