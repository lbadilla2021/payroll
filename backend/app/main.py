from datetime import datetime, timedelta, timezone
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import audit
from app.config import settings
from app.database import Base, engine, get_db
from app.deps import get_current_session, get_current_user, require_superadmin, resolve_tenant_context
from app.email_utils import send_password_reset_email
from app.models import PasswordResetToken, Tenant, User, UserSession
from app.rate_limit import check_forgot_limits, check_login_limits, check_reset_limits
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GenericMessage,
    LoginRequest,
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
    validate_password_blocklist,
    validate_password_policy,
    verify_password,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title='Payroll Chile API', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'X-Tenant-Code'],
)


@app.middleware('http')
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Cache-Control'] = 'no-store'
    return response


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_password_blocklist() -> set[str]:
    path = Path(settings.blocklist_path)
    if not path.exists():
        return set()
    return {line.strip().lower() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()}


PASSWORD_BLOCKLIST = load_password_blocklist()


def enforce_password_policy_or_raise(password: str):
    ok, reason = validate_password_policy(password)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    ok, reason = validate_password_blocklist(password, PASSWORD_BLOCKLIST)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)


def build_auth_response(user: User, session: UserSession, response: Response, refresh_token: str) -> AuthResponse:
    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, session_id=session.id, auth_version=user.auth_version)
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
    return AuthResponse(access_token=access, user=user)


def create_session(db: Session, user: User, request: Request, rotated_from: str | None = None) -> tuple[UserSession, str]:
    refresh_token = generate_refresh_token()
    current = now_utc()
    session = UserSession(
        id=generate_session_id(),
        user_id=user.id,
        tenant_id=user.tenant_id,
        refresh_token_hash=hash_opaque_token(refresh_token),
        user_agent=request.headers.get('user-agent'),
        ip_address=request.client.host if request.client else None,
        expires_at=current + timedelta(minutes=settings.session_absolute_timeout_minutes),
        idle_expires_at=current + timedelta(minutes=settings.session_idle_timeout_minutes),
        last_seen_at=current,
        rotated_from_session_id=rotated_from,
    )
    db.add(session)
    db.flush()
    return session, refresh_token


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok'}


@app.post('/api/auth/login', response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    tenant = resolve_tenant_context(request, payload.tenant_code, db)
    tenant_bucket = tenant.code if tenant else (payload.tenant_code or 'none').lower()
    ip = request.client.host if request.client else 'unknown'

    allowed, blocked_dim = check_login_limits(db, ip=ip, tenant_bucket=tenant_bucket, email=payload.email)
    if not allowed:
        audit.rate_limit_block(db, request=request, reason=f'login_{blocked_dim}', tenant_id=tenant.id if tenant else None, email_input=payload.email)
        db.commit()
        raise HTTPException(status_code=429, detail='Demasiados intentos')

    generic_error = HTTPException(status_code=401, detail='Credenciales inválidas')
    if not tenant:
        audit.login_failure(db, request=request, reason='tenant_not_found', email_input=payload.email)
        db.commit()
        raise generic_error

    user = db.query(User).filter(User.tenant_id == tenant.id, User.email_normalized == payload.email.lower(), User.is_active.is_(True)).first()
    if not user:
        audit.login_failure(db, request=request, reason='invalid_credentials', tenant_id=tenant.id, email_input=payload.email)
        db.commit()
        raise generic_error

    valid, needs_rehash = verify_password(payload.password, user.password_hash)
    if not valid:
        audit.login_failure(db, request=request, reason='invalid_credentials', tenant_id=tenant.id, user_id=user.id, email_input=payload.email)
        db.commit()
        raise generic_error

    if needs_rehash:
        user.password_hash = hash_password(payload.password)

    session, refresh_token = create_session(db, user, request)
    audit.login_success(db, request=request, tenant_id=user.tenant_id, user_id=user.id, email_input=user.email_normalized)
    db.commit()
    return build_auth_response(user, session, response, refresh_token)


@app.post('/api/auth/refresh', response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get('refresh_token')
    if not token:
        raise HTTPException(status_code=401, detail='Sesión inválida')

    session = db.query(UserSession).filter(UserSession.refresh_token_hash == hash_opaque_token(token)).first()
    if not session or session.revoked_at is not None:
        raise HTTPException(status_code=401, detail='Sesión inválida')

    now = now_utc()
    if session.idle_expires_at.replace(tzinfo=timezone.utc) < now or session.expires_at.replace(tzinfo=timezone.utc) < now:
        session.revoked_at = now
        session.revoke_reason = 'expired'
        audit.session_revoked(db, request=request, tenant_id=session.tenant_id, user_id=session.user_id, reason='expired')
        db.commit()
        raise HTTPException(status_code=401, detail='Sesión expirada')

    user = db.query(User).filter(User.id == session.user_id, User.tenant_id == session.tenant_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail='Sesión inválida')

    session.revoked_at = now
    session.revoke_reason = 'rotated'
    audit.session_revoked(db, request=request, tenant_id=user.tenant_id, user_id=user.id, reason='rotated')
    new_session, new_refresh = create_session(db, user, request, rotated_from=session.id)
    audit.refresh_success(db, request=request, tenant_id=user.tenant_id, user_id=user.id)
    db.commit()
    return build_auth_response(user, new_session, response, new_refresh)


@app.get('/api/auth/me', response_model=UserInfo)
def me(current_user: User = Depends(get_current_user), session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    session.last_seen_at = now_utc()
    session.idle_expires_at = now_utc() + timedelta(minutes=settings.session_idle_timeout_minutes)
    db.commit()
    return current_user


@app.post('/api/auth/logout', response_model=GenericMessage)
def logout(request: Request, response: Response, current_user: User = Depends(get_current_user), session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    now = now_utc()
    session.revoked_at = now
    session.revoke_reason = 'logout'
    audit.logout(db, request=request, tenant_id=current_user.tenant_id, user_id=current_user.id)
    audit.session_revoked(db, request=request, tenant_id=current_user.tenant_id, user_id=current_user.id, reason='logout')
    response.delete_cookie('refresh_token', path='/api/auth', domain=settings.cookie_domain)
    db.commit()
    return GenericMessage(message='Sesión cerrada')


@app.post('/api/auth/logout-all', response_model=GenericMessage)
def logout_all(request: Request, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = now_utc()
    db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.tenant_id == current_user.tenant_id, UserSession.revoked_at.is_(None)).update({'revoked_at': now, 'revoke_reason': 'logout_all'})
    audit.logout_all(db, request=request, tenant_id=current_user.tenant_id, user_id=current_user.id)
    audit.session_revoked(db, request=request, tenant_id=current_user.tenant_id, user_id=current_user.id, reason='logout_all')
    response.delete_cookie('refresh_token', path='/api/auth', domain=settings.cookie_domain)
    db.commit()
    return GenericMessage(message='Todas las sesiones cerradas')


@app.post('/api/auth/forgot-password', response_model=GenericMessage)
def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    tenant = resolve_tenant_context(request, payload.tenant_code, db)
    tenant_bucket = tenant.code if tenant else (payload.tenant_code or 'none').lower()
    ip = request.client.host if request.client else 'unknown'

    allowed, blocked_dim = check_forgot_limits(db, ip=ip, tenant_bucket=tenant_bucket, email=payload.email)
    if not allowed:
        audit.rate_limit_block(db, request=request, reason=f'forgot_{blocked_dim}', tenant_id=tenant.id if tenant else None, email_input=payload.email)
        db.commit()
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes')

    user = None
    if tenant:
        user = db.query(User).filter(User.tenant_id == tenant.id, User.email_normalized == payload.email.lower(), User.is_active.is_(True)).first()
        if user and settings.enable_password_recovery:
            db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).update({'used_at': now_utc()})
            raw = generate_reset_token()
            db.add(
                PasswordResetToken(
                    tenant_id=user.tenant_id,
                    user_id=user.id,
                    token_hash=hash_opaque_token(raw),
                    expires_at=now_utc() + timedelta(minutes=settings.password_reset_token_minutes),
                    requested_ip=ip,
                    requested_user_agent=request.headers.get('user-agent'),
                )
            )
            reset_link = f"{settings.app_base_url}/reset-password.html?token={raw}"
            send_password_reset_email(user.email_normalized, tenant.name, reset_link, settings.password_reset_token_minutes)

    audit.forgot_password_requested(db, request=request, tenant_id=tenant.id if tenant else None, user_id=user.id if user else None, email_input=payload.email)
    db.commit()
    return GenericMessage(message='Si la cuenta existe, recibirás un correo con instrucciones.')


@app.post('/api/auth/reset-password', response_model=GenericMessage)
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    enforce_password_policy_or_raise(payload.new_password)

    ip = request.client.host if request.client else 'unknown'
    allowed, blocked_dim = check_reset_limits(db, ip=ip, tenant_bucket='unknown')
    if not allowed:
        audit.rate_limit_block(db, request=request, reason=f'reset_{blocked_dim}')
        db.commit()
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes')

    token_hash = hash_opaque_token(payload.token)
    token_obj = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not token_obj or token_obj.used_at is not None or token_obj.expires_at.replace(tzinfo=timezone.utc) < now_utc():
        raise HTTPException(status_code=400, detail='Token inválido o expirado')

    user = db.query(User).filter(User.id == token_obj.user_id, User.tenant_id == token_obj.tenant_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=400, detail='Token inválido o expirado')

    user.password_hash = hash_password(payload.new_password)
    user.auth_version += 1
    token_obj.used_at = now_utc()
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).update({'used_at': now_utc()})
    db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.tenant_id == user.tenant_id, UserSession.revoked_at.is_(None)).update({'revoked_at': now_utc(), 'revoke_reason': 'password_reset'})
    audit.password_reset_success(db, request=request, tenant_id=user.tenant_id, user_id=user.id)
    audit.session_revoked(db, request=request, tenant_id=user.tenant_id, user_id=user.id, reason='password_reset')
    db.commit()
    return GenericMessage(message='Contraseña restablecida correctamente')


@app.post('/api/auth/change-password', response_model=GenericMessage)
def change_password(payload: ChangePasswordRequest, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enforce_password_policy_or_raise(payload.new_password)
    valid, _ = verify_password(payload.current_password, current_user.password_hash)
    if not valid:
        audit.login_failure(db, request=request, reason='invalid_current_password', tenant_id=current_user.tenant_id, user_id=current_user.id, email_input=current_user.email_normalized)
        db.commit()
        raise HTTPException(status_code=400, detail='No se pudo cambiar contraseña')

    current_user.password_hash = hash_password(payload.new_password)
    current_user.auth_version += 1
    db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.tenant_id == current_user.tenant_id, UserSession.revoked_at.is_(None)).update({'revoked_at': now_utc(), 'revoke_reason': 'password_change'})
    audit.password_change_success(db, request=request, tenant_id=current_user.tenant_id, user_id=current_user.id)
    audit.session_revoked(db, request=request, tenant_id=current_user.tenant_id, user_id=current_user.id, reason='password_change')
    db.commit()
    return GenericMessage(message='Contraseña actualizada')


@app.post('/api/admin/tenants', response_model=TenantOut)
def create_tenant(payload: TenantCreate, _: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    tenant = Tenant(name=payload.name.strip(), code=payload.code.strip().lower(), is_active=True)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@app.get('/api/admin/tenants', response_model=list[TenantOut])
def list_tenants(_: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    return db.query(Tenant).order_by(Tenant.id.desc()).all()


@app.post('/api/admin/users', response_model=UserOut)
def create_user(payload: UserCreate, _: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    enforce_password_policy_or_raise(payload.password)
    email_normalized = payload.email.lower()
    if settings.allow_global_email_uniqueness:
        exists = db.query(User).filter(User.email_normalized == email_normalized).first()
    else:
        exists = db.query(User).filter(User.tenant_id == payload.tenant_id, User.email_normalized == email_normalized).first()
    if exists:
        raise HTTPException(status_code=400, detail='El email ya existe para el ámbito configurado')

    user = User(
        tenant_id=payload.tenant_id,
        email=payload.email.strip(),
        email_normalized=email_normalized,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        is_tenant_admin=True,
        is_superadmin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
