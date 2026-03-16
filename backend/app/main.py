from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_superadmin
from app.models import Tenant, User
from app.schemas import (
    LoginRequest,
    TenantCreate,
    TenantOut,
    TokenResponse,
    UserCreate,
    UserInfo,
    UserOut,
)
from app.security import create_access_token, hash_password, verify_password

app = FastAPI(title='Payroll Chile API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok'}


@app.post('/api/auth/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Credenciales inválidas')

    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@app.get('/api/auth/me', response_model=UserInfo)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get('/api/admin/tenants', response_model=list[TenantOut])
def list_tenants(_: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    return db.query(Tenant).order_by(Tenant.id.desc()).all()


@app.post('/api/admin/tenants', response_model=TenantOut)
def create_tenant(
    payload: TenantCreate,
    _: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    exists = db.query(Tenant).filter((Tenant.name == payload.name) | (Tenant.code == payload.code)).first()
    if exists:
        raise HTTPException(status_code=400, detail='Tenant ya existe')

    tenant = Tenant(name=payload.name.strip(), code=payload.code.strip().lower())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@app.post('/api/admin/users', response_model=UserOut)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    if payload.role != 'tenant_admin':
        raise HTTPException(status_code=400, detail='Solo se permite crear tenant_admin')

    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail='Tenant no encontrado')

    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail='Email ya registrado')

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
