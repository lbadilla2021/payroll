from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin_or_superadmin, require_superadmin
from app.core.security import generate_secure_token, hash_password
from app.db.session import get_db
from app.email.service import send_welcome_email
from app.models.models import Tenant, User
from app.schemas.schemas import (
    MessageResponse, UserCreate, UserListResponse, UserResponse, UserUpdate
)
from app.services.audit import log_event

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(db: Session, user_id: UUID) -> User:
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    return u


def _assert_tenant_scope(actor: User, target_tenant_id: Optional[UUID]):
    """Admins can only manage users within their own tenant."""
    if actor.role != "superadmin":
        if target_tenant_id != actor.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied.")


def _check_quota(db: Session, tenant_id: UUID, exclude_user_id: Optional[UUID] = None):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found.")
    q = db.query(func.count(User.id)).filter(User.tenant_id == tenant_id, User.is_active == True)
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    count = q.scalar()
    if count >= tenant.max_users:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant user quota reached ({tenant.max_users} active users)."
        )


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    tenant_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    q = db.query(User)

    # Tenant isolation: admins can only see their own tenant
    if actor.role == "superadmin":
        if tenant_id:
            q = q.filter(User.tenant_id == tenant_id)
    else:
        q = q.filter(User.tenant_id == actor.tenant_id)

    if search:
        q = q.filter(
            User.email.ilike(f"%{search}%") |
            User.first_name.ilike(f"%{search}%") |
            User.last_name.ilike(f"%{search}%")
        )
    if is_active is not None:
        q = q.filter(User.is_active == is_active)

    total = q.count()
    items = q.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return UserListResponse(items=[UserResponse.model_validate(u) for u in items], total=total, page=page, size=size)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    # Scope check
    if actor.role == "admin":
        body.tenant_id = actor.tenant_id  # force to actor's tenant
        if body.role == "superadmin":
            raise HTTPException(status_code=403, detail="Cannot create superadmin.")
    elif actor.role == "superadmin" and body.role != "superadmin" and not body.tenant_id:
        raise HTTPException(status_code=400, detail="Non-superadmin users require a tenant_id.")

    # Quota check (if tenant-scoped)
    if body.tenant_id:
        _check_quota(db, body.tenant_id)

    # Uniqueness
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        password_hash=hash_password(body.password),
        role=body.role,
        tenant_id=body.tenant_id,
        username=body.username,
        phone=body.phone,
        job_title=body.job_title,
        force_password_change=body.force_password_change,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    send_welcome_email(user.email, user.first_name)
    log_event(db, "user.create", user_id=actor.id, actor_email=actor.email,
              resource_type="user", resource_id=str(user.id), tenant_id=body.tenant_id)

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    user = _get_user_or_404(db, user_id)
    _assert_tenant_scope(actor, user.tenant_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    user = _get_user_or_404(db, user_id)
    _assert_tenant_scope(actor, user.tenant_id)

    # Admins cannot elevate to superadmin
    if actor.role == "admin" and body.role == "superadmin":
        raise HTTPException(status_code=403, detail="Cannot assign superadmin role.")

    # Quota check when re-activating
    if body.is_active is True and not user.is_active and user.tenant_id:
        _check_quota(db, user.tenant_id, exclude_user_id=user_id)

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    log_event(db, "user.update", user_id=actor.id, actor_email=actor.email,
              resource_type="user", resource_id=str(user.id))
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    user = _get_user_or_404(db, user_id)
    _assert_tenant_scope(actor, user.tenant_id)

    if not user.is_active and user.tenant_id:
        _check_quota(db, user.tenant_id, exclude_user_id=user_id)

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    action = "user.activate" if user.is_active else "user.deactivate"
    log_event(db, action, user_id=actor.id, resource_type="user", resource_id=str(user.id))
    return UserResponse.model_validate(user)


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
def admin_reset_password(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    """Admin sets a temporary password and forces change on next login."""
    user = _get_user_or_404(db, user_id)
    _assert_tenant_scope(actor, user.tenant_id)

    temp_pwd = generate_secure_token(12)
    user.password_hash = hash_password(temp_pwd)
    user.force_password_change = True
    db.commit()

    send_welcome_email(user.email, user.first_name, temp_pwd)
    log_event(db, "user.admin_password_reset", user_id=actor.id, actor_email=actor.email,
              resource_type="user", resource_id=str(user.id))
    return {"message": f"Temporary password sent to {user.email}."}
