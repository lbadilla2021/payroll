"""
Rate limiting for sensitive endpoints.

Current: in-memory (suitable for single-process dev).
Production path: swap _store for Redis with the same interface.
"""

import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, status

from app.core.config import settings

# {key: [(timestamp, count)]}
_store: dict[str, list] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    now = time.time()
    window_start = now - window_seconds
    attempts = _store[key]
    # clean old entries
    _store[key] = [t for t in attempts if t > window_start]
    if len(_store[key]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(window_seconds)},
        )
    _store[key].append(now)


def login_rate_limit(request: Request) -> None:
    ip = _get_client_ip(request)
    check_rate_limit(
        f"login:{ip}",
        settings.LOGIN_RATE_LIMIT,
        settings.LOGIN_RATE_WINDOW_SECONDS,
    )


def password_reset_rate_limit(request: Request) -> None:
    ip = _get_client_ip(request)
    check_rate_limit(
        f"pwd_reset:{ip}",
        settings.PASSWORD_RESET_RATE_LIMIT,
        settings.PASSWORD_RESET_RATE_WINDOW_SECONDS,
    )
