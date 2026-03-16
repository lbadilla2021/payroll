import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


PBKDF2_ALGORITHM = 'sha256'
PBKDF2_ITERATIONS = 390000
HASH_PREFIX = 'pbkdf2_sha256'


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')


def _b64_decode(raw: str) -> bytes:
    padded = raw + '=' * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode('utf-8'))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode('utf-8'),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f'{HASH_PREFIX}${PBKDF2_ITERATIONS}${_b64_encode(salt)}${_b64_encode(digest)}'


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        prefix, iter_text, salt_text, digest_text = hashed_password.split('$', 3)
        if prefix != HASH_PREFIX:
            return False
        iterations = int(iter_text)
        salt = _b64_decode(salt_text)
        expected_digest = _b64_decode(digest_text)

        computed_digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode('utf-8'),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_digest, expected_digest)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes)
    payload = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError('Invalid token') from exc
