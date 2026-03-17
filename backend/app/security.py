import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

PBKDF2_ALGORITHM = 'sha256'
PBKDF2_ITERATIONS = 390000
PBKDF2_PREFIX = 'pbkdf2_sha256'
SCRYPT_PREFIX = 'scrypt_sha256'


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')


def _b64_decode(raw: str) -> bytes:
    padded = raw + '=' * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode('utf-8'))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1)
    return f'{SCRYPT_PREFIX}$16384$8$1${_b64_encode(salt)}${_b64_encode(digest)}'


def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, bool]:
    if hashed_password.startswith(SCRYPT_PREFIX):
        try:
            _, n, r, p, salt_text, digest_text = hashed_password.split('$', 5)
            salt = _b64_decode(salt_text)
            expected_digest = _b64_decode(digest_text)
            digest = hashlib.scrypt(plain_password.encode('utf-8'), salt=salt, n=int(n), r=int(r), p=int(p))
            return hmac.compare_digest(digest, expected_digest), False
        except Exception:
            return False, False

    try:
        prefix, iter_text, salt_text, digest_text = hashed_password.split('$', 3)
        if prefix != PBKDF2_PREFIX:
            return False, False
        iterations = int(iter_text)
        salt = _b64_decode(salt_text)
        expected_digest = _b64_decode(digest_text)
        computed_digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, plain_password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(computed_digest, expected_digest), True
    except Exception:
        return False, False


def create_access_token(subject: str, tenant_id: int | None, session_id: str, auth_version: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {'sub': subject, 'tenant_id': tenant_id, 'sid': session_id, 'ver': auth_version, 'exp': expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError('Invalid token') from exc


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def generate_session_id() -> str:
    return secrets.token_urlsafe(24)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def generate_reset_token() -> str:
    return secrets.token_urlsafe(48)
