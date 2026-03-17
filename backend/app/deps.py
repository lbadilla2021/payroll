from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, User, UserSession
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


def resolve_tenant_context(request: Request, tenant_code: str | None, db: Session) -> Tenant | None:
    code = (tenant_code or request.headers.get('x-tenant-code') or '').strip().lower()
    if not code:
        host = (request.headers.get('host') or '').split(':')[0]
        parts = host.split('.')
        if len(parts) > 2 and parts[0] not in {'www', 'localhost'}:
            code = parts[0].lower()
    if not code:
        return None
    return db.query(Tenant).filter(Tenant.code == code, Tenant.is_active.is_(True)).first()


def get_current_session(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserSession:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Sesión inválida')
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get('sub'))
        tid_claim = payload.get('tid')
        tenant_id = None if tid_claim == 'global' else int(tid_claim)
        session_id = payload.get('sid')
        token_ver = int(payload.get('ver'))
        if not session_id:
            raise credentials_error
    except Exception as exc:
        raise credentials_error from exc

    session = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == user_id, UserSession.tenant_id == tenant_id)
        .first()
    )
    now = datetime.now(timezone.utc)
    if not session or session.revoked_at is not None:
        raise credentials_error
    if session.idle_expires_at.replace(tzinfo=timezone.utc) < now or session.expires_at.replace(tzinfo=timezone.utc) < now:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id, User.is_active.is_(True)).first()
    if not user or user.auth_version != token_ver:
        raise credentials_error

    request.state.token_payload = payload
    request.state.current_user = user
    request.state.current_session = session
    return session


def get_current_user(
    request: Request,
    _: UserSession = Depends(get_current_session),
) -> User:
    return request.state.current_user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superadmin:
        raise HTTPException(status_code=403, detail='Superadmin access required')
    return user


def require_tenant_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_tenant_admin and not user.is_superadmin:
        raise HTTPException(status_code=403, detail='Tenant admin access required')
    return user
