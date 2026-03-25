from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_superadmin
from app.db.session import get_db
from app.models.models import Tenant, User
from app.schemas.schemas import (
    MessageResponse, TenantCreate, TenantListResponse, TenantResponse, TenantUpdate
)
from app.services.audit import log_event
from app.services.rbac import ensure_system_roles_for_tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _get_tenant_or_404(db: Session, tenant_id: UUID) -> Tenant:
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    return t


def _to_response(tenant: Tenant, db: Session) -> TenantResponse:
    count = db.query(func.count(User.id)).filter(
        User.tenant_id == tenant.id, User.is_active == True
    ).scalar()
    data = TenantResponse.model_validate(tenant)
    data.user_count = count
    return data


@router.get("", response_model=TenantListResponse)
def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    q = db.query(Tenant)
    if search:
        q = q.filter(Tenant.name.ilike(f"%{search}%") | Tenant.slug.ilike(f"%{search}%"))
    if is_active is not None:
        q = q.filter(Tenant.is_active == is_active)
    total = q.count()
    items = q.order_by(Tenant.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return TenantListResponse(
        items=[_to_response(t, db) for t in items],
        total=total, page=page, size=size,
    )


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    request: Request,
    body: TenantCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_superadmin),
):
    if db.query(Tenant).filter(Tenant.slug == body.slug).first():
        raise HTTPException(status_code=400, detail="Slug already in use.")
    tenant = Tenant(**body.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    ensure_system_roles_for_tenant(tenant.id, db)
    log_event(db, "tenant.create", user_id=actor.id, actor_email=actor.email,
              resource_type="tenant", resource_id=str(tenant.id))
    return _to_response(tenant, db)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return _to_response(_get_tenant_or_404(db, tenant_id), db)


@router.patch("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    request: Request,
    tenant_id: UUID,
    body: TenantUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_superadmin),
):
    tenant = _get_tenant_or_404(db, tenant_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(tenant, k, v)
    db.commit()
    db.refresh(tenant)
    log_event(db, "tenant.update", user_id=actor.id, actor_email=actor.email,
              resource_type="tenant", resource_id=str(tenant.id))
    return _to_response(tenant, db)


@router.patch("/{tenant_id}/toggle-active", response_model=TenantResponse)
def toggle_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_superadmin),
):
    tenant = _get_tenant_or_404(db, tenant_id)
    tenant.is_active = not tenant.is_active
    db.commit()
    db.refresh(tenant)
    action = "tenant.activate" if tenant.is_active else "tenant.deactivate"
    log_event(db, action, user_id=actor.id, resource_type="tenant", resource_id=str(tenant.id))
    return _to_response(tenant, db)