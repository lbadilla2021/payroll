import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
from jose import JWTError, jwt

from app.config import settings

PBKDF2_ALGORITHM = 'sha256'
PBKDF2_PREFIX = 'pbkdf2_sha256'
SCRYPT_PREFIX = 'scrypt_sha256'
pwd_hasher = PasswordHasher()


def _b64_decode(raw: str) -> bytes:
    padded = raw + '=' * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode('utf-8'))


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def _verify_legacy_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(SCRYPT_PREFIX):
        try:
            _, n, r, p, salt_text, digest_text = hashed_password.split('$', 5)
            salt = _b64_decode(salt_text)
            expected_digest = _b64_decode(digest_text)
            digest = hashlib.scrypt(plain_password.encode('utf-8'), salt=salt, n=int(n), r=int(r), p=int(p))
            return hmac.compare_digest(digest, expected_digest)
        except Exception:
            return False

    if hashed_password.startswith(PBKDF2_PREFIX):
        try:
            _, iter_text, salt_text, digest_text = hashed_password.split('$', 3)
            salt = _b64_decode(salt_text)
            expected_digest = _b64_decode(digest_text)
            digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, plain_password.encode('utf-8'), salt, int(iter_text))
            return hmac.compare_digest(digest, expected_digest)
        except Exception:
            return False

    return False


def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, bool]:
    if hashed_password.startswith('$argon2'):
        try:
            ok = pwd_hasher.verify(hashed_password, plain_password)
            return ok, pwd_hasher.check_needs_rehash(hashed_password)
        except (VerifyMismatchError, InvalidHash):
            return False, False

    ok = _verify_legacy_password(plain_password, hashed_password)
    return ok, ok


def create_access_token(*, user_id: int, tenant_id: int | None, session_id: str, auth_version: int) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.access_token_minutes)
    payload = {
        'sub': str(user_id),
        'tid': str(tenant_id) if tenant_id is not None else 'global',
        'sid': session_id,
        'ver': auth_version,
        'iss': settings.jwt_issuer,
        'aud': settings.jwt_audience,
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError as exc:
        raise ValueError('Invalid token') from exc


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(64)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def safe_compare_hash(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_opaque_token(token), token_hash)


def validate_password_policy(password: str) -> tuple[bool, str | None]:
    if len(password) < settings.password_min_length:
        return False, f'La contraseña debe tener al menos {settings.password_min_length} caracteres'
    return True, None


def validate_password_blocklist(password: str, blocklist: set[str]) -> tuple[bool, str | None]:
    if password.lower().strip() in blocklist:
        return False, 'La contraseña no está permitida'
    return True, None
