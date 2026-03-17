from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import settings


@dataclass
class RateLimiter:
    windows: dict[str, deque]

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        bucket = self.windows[key]
        now = datetime.now(timezone.utc)
        while bucket and (now - bucket[0]).total_seconds() > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


rate_limiter = RateLimiter(defaultdict(deque))


def allow_login(ip: str, tenant_bucket: str, email: str) -> bool:
    return all(
        [
            rate_limiter.allow(f'login:ip:{ip}', settings.login_max_attempts * 3, settings.login_window_minutes * 60),
            rate_limiter.allow(
                f'login:tenant:{tenant_bucket}', settings.login_max_attempts * 10, settings.login_window_minutes * 60
            ),
            rate_limiter.allow(
                f'login:acct:{tenant_bucket}:{email.lower()}', settings.login_max_attempts, settings.login_window_minutes * 60
            ),
        ]
    )


def allow_forgot_password(ip: str, tenant_bucket: str, email: str) -> bool:
    return all(
        [
            rate_limiter.allow(f'forgot:ip:{ip}', settings.password_reset_requests_per_hour * 3, 3600),
            rate_limiter.allow(f'forgot:tenant:{tenant_bucket}', settings.password_reset_requests_per_hour * 10, 3600),
            rate_limiter.allow(
                f'forgot:acct:{tenant_bucket}:{email.lower()}', settings.password_reset_requests_per_hour, 3600
            ),
        ]
    )
