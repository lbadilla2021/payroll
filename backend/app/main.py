import json
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, require_superadmin
from app.email_utils import send_password_reset_email
from app.models import AuthAuditLog, PasswordResetToken, Tenant, User, UserSession
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GenericMessage,
    LoginRequest,
    LogoutRequest,
    ResetPasswordRequest,
    TenantCreate,
    TenantOut,
    UserCreate,
    UserInfo,
    UserOut,
)
from app.security import (
    create_access_token,
    generate_refresh_token,
    generate_reset_token,
    generate_session_id,
    hash_opaque_token,
    hash_password,
    verify_password,
)

app = FastAPI(title='Payroll Chile API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(',') if origin.strip()],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'X-Tenant-Code'],
)

rate_windows = defaultdict(deque)
blocklist = {line.strip().lower() for line in Path(settings.blocklist_path).read_text(encoding='utf-8').splitlines() if line.strip()}


def now_utc():
    return datetime.now(timezone.utc)


def audit(db: Session, *, event_type: str, outcome: str, reason: str | None, tenant_id: int | None, user_id: int | None, email: str | None, request: Request):
    db.add(
        AuthAuditLog(
            event_type=event_type,
            outcome=outcome,
            reason=reason,
            tenant_id=tenant_id,
            user_id=user_id,
            email=(email or '').lower() if email else None,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            metadata_json=json.dumps({'path': str(request.url.path)}),
        )
    )


def throttle(key: str, max_attempts: int, window_seconds: int):
    q = rate_windows[key]
    now = now_utc()
    while q and (now - q[0]).total_seconds() > window_seconds:
        q.popleft()
    if len(q) >= max_attempts:
        return False
    q.append(now)
    return True


def resolve_tenant_code(payload_tenant: str | None, request: Request) -> str | None:
    if payload_tenant:
        return payload_tenant.strip().lower()
    header_tenant = request.headers.get('x-tenant-code')
    if header_tenant:
        return header_tenant.strip().lower()
    host = (request.headers.get('host') or '').split(':')[0]
    parts = host.split('.')
    if len(parts) > 2 and parts[0] not in {'www', 'localhost'}:
        return parts[0].lower()
    return None


def get_tenant(db: Session, tenant_code: str | None) -> Tenant | None:
    if not tenant_code:
        return None
    return db.query(Tenant).filter(Tenant.code == tenant_code, Tenant.is_active.is_(True)).first()


def enforce_password_policy(password: str):
    if len(password) < settings.password_min_length:
        raise HTTPException(status_code=400, detail='Contraseña no cumple política mínima')
    if password.lower() in blocklist:
        raise HTTPException(status_code=400, detail='Contraseña no permitida')


def issue_session(response: Response, user: User, request: Request, db: Session) -> AuthResponse:
    refresh_token = generate_refresh_token()
    session_id = generate_session_id()
    current = now_utc()
    session = UserSession(
        session_id=session_id,
        user_id=user.id,
        tenant_id=user.tenant_id,
        refresh_token_hash=hash_opaque_token(refresh_token),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
        expires_at=current + timedelta(minutes=settings.session_idle_timeout_minutes),
        absolute_expires_at=current + timedelta(days=settings.session_absolute_timeout_days),
    )
    db.add(session)
    db.flush()

    access_token = create_access_token(user.email, user.tenant_id, session_id, user.auth_version)
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        max_age=int(timedelta(days=settings.refresh_token_days).total_seconds()),
        path='/api/auth',
    )
    return AuthResponse(access_token=access_token, user=user)


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok'}


@app.post('/api/auth/login', response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    tenant_code = resolve_tenant_code(payload.tenant_code, request)
    tenant = get_tenant(db, tenant_code)

    ip = request.client.host if request.client else 'unknown'
    tenant_bucket = tenant.code if tenant else tenant_code or 'none'
    if not throttle(f'login:ip:{ip}', settings.login_max_attempts * 3, settings.login_window_minutes * 60):
        raise HTTPException(status_code=429, detail='Demasiados intentos')
    if not throttle(f'login:tenant:{tenant_bucket}', settings.login_max_attempts * 10, settings.login_window_minutes * 60):
        raise HTTPException(status_code=429, detail='Demasiados intentos')
    if not throttle(f'login:acct:{tenant_bucket}:{payload.email}', settings.login_max_attempts, settings.login_window_minutes * 60):
        raise HTTPException(status_code=429, detail='Demasiados intentos')

    query = db.query(User).filter(User.email == payload.email, User.is_active.is_(True))
    if tenant:
        query = query.filter(User.tenant_id == tenant.id)
    else:
        query = query.filter(User.role == 'superadmin')
    user = query.first()

    generic = HTTPException(status_code=401, detail='Credenciales inválidas')
    if not user:
        audit(db, event_type='login', outcome='failure', reason='invalid_credentials', tenant_id=tenant.id if tenant else None, user_id=None, email=payload.email, request=request)
        db.commit()
        raise generic

    ok, needs_rehash = verify_password(payload.password, user.password_hash)
    if not ok:
        audit(db, event_type='login', outcome='failure', reason='invalid_credentials', tenant_id=user.tenant_id, user_id=user.id, email=payload.email, request=request)
        db.commit()
        raise generic

    if needs_rehash:
        user.password_hash = hash_password(payload.password)

    auth = issue_session(response, user, request, db)
    audit(db, event_type='login', outcome='success', reason='ok', tenant_id=user.tenant_id, user_id=user.id, email=user.email, request=request)
    db.commit()
    return auth


@app.post('/api/auth/refresh', response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=401, detail='Sesión inválida')

    token_hash = hash_opaque_token(refresh_token)
    session = db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash, UserSession.revoked_at.is_(None)).first()
    if not session:
        raise HTTPException(status_code=401, detail='Sesión inválida')

    current = now_utc()
    if session.expires_at.replace(tzinfo=timezone.utc) < current or session.absolute_expires_at.replace(tzinfo=timezone.utc) < current:
        session.revoked_at = current
        session.revoke_reason = 'expired'
        db.commit()
        raise HTTPException(status_code=401, detail='Sesión expirada')

    user = db.query(User).filter(User.id == session.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail='Sesión inválida')

    session.revoked_at = current
    session.revoke_reason = 'rotated'
    auth = issue_session(response, user, request, db)
    audit(db, event_type='refresh', outcome='success', reason='rotated', tenant_id=user.tenant_id, user_id=user.id, email=user.email, request=request)
    db.commit()
    return auth


@app.get('/api/auth/me', response_model=UserInfo)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post('/api/auth/logout', response_model=GenericMessage)
def logout(payload: LogoutRequest, request: Request, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current = now_utc()
    if payload.all_sessions:
        db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.revoked_at.is_(None)).update({'revoked_at': current, 'revoke_reason': 'logout_all'})
        event = 'logout_all'
    else:
        sid = getattr(request.state, 'session_id', None)
        db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.session_id == sid, UserSession.revoked_at.is_(None)).update({'revoked_at': current, 'revoke_reason': 'logout'})
        event = 'logout'

    response.delete_cookie('refresh_token', path='/api/auth', domain=settings.cookie_domain)
    audit(db, event_type=event, outcome='success', reason='ok', tenant_id=current_user.tenant_id, user_id=current_user.id, email=current_user.email, request=request)
    db.commit()
    return GenericMessage(message='Sesión cerrada')


@app.post('/api/auth/forgot-password', response_model=GenericMessage)
def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    tenant_code = resolve_tenant_code(payload.tenant_code, request)
    tenant = get_tenant(db, tenant_code)
    bucket = tenant.code if tenant else tenant_code or 'none'

    ip = request.client.host if request.client else 'unknown'
    if not throttle(f'forgot:ip:{ip}', settings.password_reset_requests_per_hour * 3, 3600):
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes')
    if not throttle(f'forgot:tenant:{bucket}', settings.password_reset_requests_per_hour * 10, 3600):
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes')
    if not throttle(f'forgot:acct:{bucket}:{payload.email}', settings.password_reset_requests_per_hour, 3600):
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes')

    query = db.query(User).filter(User.email == payload.email, User.is_active.is_(True))
    if tenant:
        query = query.filter(User.tenant_id == tenant.id)
    else:
        query = query.filter(User.role == 'superadmin')
    user = query.first()

    if user:
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.consumed_at.is_(None)).update({'consumed_at': now_utc()})
        raw = generate_reset_token()
        prt = PasswordResetToken(
            tenant_id=user.tenant_id,
            user_id=user.id,
            email=user.email,
            token_hash=hash_opaque_token(raw),
            expires_at=now_utc() + timedelta(minutes=settings.password_reset_token_minutes),
        )
        db.add(prt)
        reset_link = f"{settings.app_base_url}/reset-password.html?token={raw}"
        send_password_reset_email(user.email, tenant_code, reset_link)

    audit(db, event_type='forgot_password', outcome='accepted', reason='generic_response', tenant_id=tenant.id if tenant else None, user_id=user.id if user else None, email=payload.email, request=request)
    db.commit()
    return GenericMessage(message='Si la cuenta existe, recibirás un correo con instrucciones.')


@app.post('/api/auth/reset-password', response_model=GenericMessage)
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    enforce_password_policy(payload.new_password)
    token_hash = hash_opaque_token(payload.token)
    token_obj = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not token_obj or token_obj.consumed_at is not None or token_obj.expires_at.replace(tzinfo=timezone.utc) < now_utc():
        raise HTTPException(status_code=400, detail='Token inválido o expirado')

    user = db.query(User).filter(User.id == token_obj.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=400, detail='Token inválido o expirado')

    user.password_hash = hash_password(payload.new_password)
    user.auth_version += 1
    user.password_changed_at = now_utc()
    token_obj.consumed_at = now_utc()
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.consumed_at.is_(None)).update({'consumed_at': now_utc()})
    db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)).update({'revoked_at': now_utc(), 'revoke_reason': 'password_reset'})
    audit(db, event_type='password_reset', outcome='success', reason='token_consumed', tenant_id=user.tenant_id, user_id=user.id, email=user.email, request=request)
    db.commit()
    return GenericMessage(message='Contraseña restablecida correctamente.')


@app.post('/api/auth/change-password', response_model=GenericMessage)
def change_password(payload: ChangePasswordRequest, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enforce_password_policy(payload.new_password)
    ok, _ = verify_password(payload.current_password, current_user.password_hash)
    if not ok:
        audit(db, event_type='change_password', outcome='failure', reason='invalid_current_password', tenant_id=current_user.tenant_id, user_id=current_user.id, email=current_user.email, request=request)
        db.commit()
        raise HTTPException(status_code=400, detail='No se pudo cambiar contraseña')

    current_user.password_hash = hash_password(payload.new_password)
    current_user.auth_version += 1
    current_user.password_changed_at = now_utc()
    db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.revoked_at.is_(None)).update({'revoked_at': now_utc(), 'revoke_reason': 'password_change'})
    audit(db, event_type='change_password', outcome='success', reason='ok', tenant_id=current_user.tenant_id, user_id=current_user.id, email=current_user.email, request=request)
    db.commit()
    return GenericMessage(message='Contraseña actualizada. Debes volver a iniciar sesión.')


@app.get('/api/admin/tenants', response_model=list[TenantOut])
def list_tenants(_: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    return db.query(Tenant).order_by(Tenant.id.desc()).all()


@app.post('/api/admin/tenants', response_model=TenantOut)
def create_tenant(payload: TenantCreate, _: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    exists = db.query(Tenant).filter((Tenant.name == payload.name) | (Tenant.code == payload.code)).first()
    if exists:
        raise HTTPException(status_code=400, detail='Tenant ya existe')
    tenant = Tenant(name=payload.name.strip(), code=payload.code.strip().lower())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@app.post('/api/admin/users', response_model=UserOut)
def create_user(payload: UserCreate, _: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    if payload.role != 'tenant_admin':
        raise HTTPException(status_code=400, detail='Solo se permite crear tenant_admin')

    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail='Tenant no encontrado')

    enforce_password_policy(payload.password)
    exists = db.query(User).filter(User.email == payload.email, User.tenant_id == tenant.id).first()
    if exists:
        raise HTTPException(status_code=400, detail='Email ya registrado en tenant')

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role='tenant_admin',
        tenant_id=tenant.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
