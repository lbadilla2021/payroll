"""
Rate limiting with Redis backend.

Uses Redis INCR + EXPIRE for atomic, multi-process-safe counters.
Falls back to in-memory if Redis is unavailable (dev convenience).

Algorithm: Fixed window counter
- Key: "rl:{endpoint}:{ip}"
- On each request: INCR the key, set EXPIRE if new key
- If count > limit: return 429

For production, sliding window log is more accurate but costs more memory.
Fixed window is sufficient for login brute-force protection.
"""

import time
import logging
from collections import defaultdict
from typing import Optional

import redis as redis_lib
from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Redis connection ──────────────────────────────────────────────────────────

_redis: Optional[redis_lib.Redis] = None

def _get_redis() -> Optional[redis_lib.Redis]:
    """Lazy singleton Redis connection. Returns None if unavailable."""
    global _redis
    if _redis is not None:
        try:
            _redis.ping()
            return _redis
        except Exception:
            _redis = None

    try:
        _redis = redis_lib.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis.ping()
        logger.info("Rate limiter: connected to Redis")
        return _redis
    except Exception as e:
        logger.warning(f"Rate limiter: Redis unavailable ({e}), falling back to memory")
        return None


# ── In-memory fallback ────────────────────────────────────────────────────────

_memory_store: dict[str, list] = defaultdict(list)

def _check_memory(key: str, limit: int, window_seconds: int) -> None:
    """Fallback rate limiter using in-memory store."""
    now = time.time()
    window_start = now - window_seconds
    _memory_store[key] = [t for t in _memory_store[key] if t > window_start]
    if len(_memory_store[key]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(window_seconds)},
        )
    _memory_store[key].append(now)


# ── Core rate limit check ─────────────────────────────────────────────────────

def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """
    Check rate limit. Raises HTTP 429 if exceeded.
    Uses Redis if available, in-memory fallback otherwise.
    """
    r = _get_redis()

    if r is None:
        _check_memory(key, limit, window_seconds)
        return

    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)  # sets TTL only if not already set
        results = pipe.execute()
        count = results[0]

        if count > limit:
            ttl = r.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
                headers={"Retry-After": str(max(ttl, window_seconds))},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redis rate limit error: {e}, falling back to memory")
        _check_memory(key, limit, window_seconds)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    return xff.split(",")[0].strip() if xff else (
        request.client.host if request.client else "unknown"
    )


# ── Endpoint-specific limiters ────────────────────────────────────────────────

def login_rate_limit(request: Request) -> None:
    ip = _get_ip(request)
    check_rate_limit(
        f"rl:login:{ip}",
        settings.LOGIN_RATE_LIMIT,
        settings.LOGIN_RATE_WINDOW_SECONDS,
    )


def password_reset_rate_limit(request: Request) -> None:
    ip = _get_ip(request)
    check_rate_limit(
        f"rl:pwd_reset:{ip}",
        settings.PASSWORD_RESET_RATE_LIMIT,
        settings.PASSWORD_RESET_RATE_WINDOW_SECONDS,
    )