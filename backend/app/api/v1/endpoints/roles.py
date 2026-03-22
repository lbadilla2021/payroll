"""
Tenant Roles endpoint.

Full CRUD for tenant_roles plus:
  - SET permissions on a role  (PUT /roles/{id}/permissions)
  - GET/PUT user-role assignments  (GET|PUT /roles/{id}/users)
  - GET roles for a user  (GET /users/{user_id}/roles)
  - Assign roles to a user  (PUT /users/{user_id}/roles)

All state-change operations:
  - Require appropriate permission via require_permission()
  - Write to audit_log
  - Invalidate Redis permission cache for affected users
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.models.models import (
    Permission, Tenant, TenantRole, TenantRolePermission, User, UserTenantRole,
)
from app.schemas.schemas import (
    MessageResponse,
    RolePermissionsSet,
    TenantRoleCreate,
    TenantRoleListResponse,
    TenantRolePermissionResponse,
    TenantRoleResponse,
    TenantRoleUpdate,
    UserRoleAssign,
    UserRolesResponse,
    UserTenantRoleResponse,
)
from app.services.audit import log_event
from app.services.rbac import invalidate_role_users_cache, invalidate_user_permissions_cache

router = APIRouter(tags=["roles"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_role_or_404(db: Session, role_id: UUID) -> TenantRole:
    role = db.query(TenantRole).filter(TenantRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    return role


def _assert_tenant_scope(actor: User, role: TenantRole):
    """Ensure non-superadmin actors can only touch their own tenant's roles."""
    if actor.role != "superadmin" and role.tenant_id != actor.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")


def _assert_role_editable(role: TenantRole):
    """System roles cannot be deleted or renamed."""
    if role.is_system:
        raise HTTPException(
            status_code=403,
            detail="Los roles de sistema no pueden modificarse.",
        )


def _build_role_response(role: TenantRole, db: Session) -> TenantRoleResponse:
    """Build TenantRoleResponse with permissions and user_count eager-loaded."""
    from sqlalchemy import func as sa_func
    permissions = [
        TenantRolePermissionResponse(
            id=trp.permission.id,
            code=trp.permission.code,
            name=trp.permission.name,
            module=trp.permission.module,
        )
        for trp in role.role_permissions
        if trp.permission and trp.permission.is_active
    ]
    user_count = (
        db.query(sa_func.count(UserTenantRole.user_id))
        .filter(UserTenantRole.tenant_role_id == role.id)
        .scalar()
    )
    return TenantRoleResponse(
        id=role.id,
        tenant_id=role.tenant_id,
        name=role.name,
        description=role.description,
        is_active=role.is_active,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=permissions,
        user_count=user_count,
    )


# ── Tenant Roles CRUD ─────────────────────────────────────────────────────────

@router.get("/roles", response_model=TenantRoleListResponse)
def list_roles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.view")),
):
    """List roles for a tenant. Admins see only their tenant's roles."""
    q = db.query(TenantRole)

    if actor.role == "superadmin":
        if tenant_id:
            q = q.filter(TenantRole.tenant_id == tenant_id)
    else:
        q = q.filter(TenantRole.tenant_id == actor.tenant_id)

    if search:
        q = q.filter(TenantRole.name.ilike(f"%{search}%"))
    if is_active is not None:
        q = q.filter(TenantRole.is_active == is_active)

    total = q.count()
    roles = q.order_by(TenantRole.name).offset((page - 1) * size).limit(size).all()
    items = [_build_role_response(r, db) for r in roles]

    return TenantRoleListResponse(items=items, total=total, page=page, size=size)


@router.post("/roles", response_model=TenantRoleResponse, status_code=201)
def create_role(
    body: TenantRoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.create")),
):
    """Create a new custom role for the actor's tenant."""
    # Determine target tenant
    target_tenant_id = actor.tenant_id
    if actor.role == "superadmin":
        raise HTTPException(
            status_code=400,
            detail="Superadmin debe especificar tenant_id como query param.",
        )

    # Duplicate name check
    existing = db.query(TenantRole).filter(
        TenantRole.tenant_id == target_tenant_id,
        TenantRole.name == body.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Ya existe un rol con el nombre '{body.name}' en este tenant.")

    role = TenantRole(
        tenant_id=target_tenant_id,
        name=body.name,
        description=body.description,
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()

    # Assign initial permissions if provided
    if body.permission_ids:
        _set_role_permissions(role, body.permission_ids, db)

    db.commit()
    db.refresh(role)

    log_event(
        db,
        action="role.create",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=target_tenant_id,
        resource_type="tenant_role",
        resource_id=str(role.id),
        detail={"name": role.name, "permission_count": len(body.permission_ids)},
        ip_address=request.client.host if request.client else None,
    )

    return _build_role_response(role, db)


@router.post("/roles/superadmin", response_model=TenantRoleResponse, status_code=201)
def create_role_for_tenant(
    body: TenantRoleCreate,
    tenant_id: UUID = Query(...),
    request: Request = None,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.tenants.edit")),
):
    """Superadmin-only: create a role for any tenant."""
    if actor.role != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede usar este endpoint.")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado.")

    existing = db.query(TenantRole).filter(
        TenantRole.tenant_id == tenant_id,
        TenantRole.name == body.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Ya existe un rol con el nombre '{body.name}' en este tenant.")

    role = TenantRole(
        tenant_id=tenant_id,
        name=body.name,
        description=body.description,
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()

    if body.permission_ids:
        _set_role_permissions(role, body.permission_ids, db)

    db.commit()
    db.refresh(role)

    log_event(
        db,
        action="role.create",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=tenant_id,
        resource_type="tenant_role",
        resource_id=str(role.id),
        detail={"name": role.name, "created_for_tenant": str(tenant_id)},
        ip_address=request.client.host if request and request.client else None,
    )

    return _build_role_response(role, db)


@router.get("/roles/{role_id}", response_model=TenantRoleResponse)
def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.view")),
):
    role = _get_role_or_404(db, role_id)
    _assert_tenant_scope(actor, role)
    return _build_role_response(role, db)


@router.patch("/roles/{role_id}", response_model=TenantRoleResponse)
def update_role(
    role_id: UUID,
    body: TenantRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.edit")),
):
    role = _get_role_or_404(db, role_id)
    _assert_tenant_scope(actor, role)

    # is_active can be toggled even on system roles; name/description cannot
    if body.name is not None or body.description is not None:
        _assert_role_editable(role)

    if body.name is not None and body.name != role.name:
        dup = db.query(TenantRole).filter(
            TenantRole.tenant_id == role.tenant_id,
            TenantRole.name == body.name,
            TenantRole.id != role_id,
        ).first()
        if dup:
            raise HTTPException(status_code=409, detail=f"Ya existe un rol con el nombre '{body.name}'.")
        role.name = body.name

    if body.description is not None:
        role.description = body.description
    if body.is_active is not None:
        role.is_active = body.is_active

    db.commit()
    db.refresh(role)

    # Invalidate cache for all users with this role
    invalidate_role_users_cache(role_id, db)

    log_event(
        db,
        action="role.update",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=role.tenant_id,
        resource_type="tenant_role",
        resource_id=str(role_id),
        detail=body.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    )

    return _build_role_response(role, db)


@router.delete("/roles/{role_id}", response_model=MessageResponse)
def delete_role(
    role_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.delete")),
):
    role = _get_role_or_404(db, role_id)
    _assert_tenant_scope(actor, role)
    _assert_role_editable(role)

    # Invalidate cache before deletion
    invalidate_role_users_cache(role_id, db)

    role_name = role.name
    tenant_id = role.tenant_id
    db.delete(role)
    db.commit()

    log_event(
        db,
        action="role.delete",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=tenant_id,
        resource_type="tenant_role",
        resource_id=str(role_id),
        detail={"name": role_name},
        ip_address=request.client.host if request.client else None,
    )

    return MessageResponse(message=f"Rol '{role_name}' eliminado.")


# ── Role Permissions ──────────────────────────────────────────────────────────

def _set_role_permissions(role: TenantRole, permission_ids: list[UUID], db: Session):
    """Replace the full permission set of a role (within the same DB session)."""
    # Validate all permission IDs exist
    perms = db.query(Permission).filter(
        Permission.id.in_([str(pid) for pid in permission_ids]),
        Permission.is_active == True,  # noqa: E712
    ).all()
    if len(perms) != len(permission_ids):
        raise HTTPException(status_code=400, detail="Uno o más permission_ids no son válidos o están inactivos.")

    # Delete existing assignments
    db.query(TenantRolePermission).filter(
        TenantRolePermission.tenant_role_id == role.id
    ).delete(synchronize_session="fetch")

    # Insert new assignments
    for perm in perms:
        db.add(TenantRolePermission(
            tenant_role_id=role.id,
            permission_id=perm.id,
        ))


@router.put("/roles/{role_id}/permissions", response_model=TenantRoleResponse)
def set_role_permissions(
    role_id: UUID,
    body: RolePermissionsSet,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.edit")),
):
    """Replace the full permission set for a role."""
    role = _get_role_or_404(db, role_id)
    _assert_tenant_scope(actor, role)

    old_count = len(role.role_permissions)
    _set_role_permissions(role, body.permission_ids, db)
    db.commit()
    db.refresh(role)

    # Invalidate cache for all users with this role
    invalidate_role_users_cache(role_id, db)

    log_event(
        db,
        action="role.permissions.set",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=role.tenant_id,
        resource_type="tenant_role",
        resource_id=str(role_id),
        detail={"old_count": old_count, "new_count": len(body.permission_ids)},
        ip_address=request.client.host if request.client else None,
    )

    return _build_role_response(role, db)


# ── User Role Assignment ──────────────────────────────────────────────────────

@router.get("/users/{user_id}/roles", response_model=UserRolesResponse)
def get_user_roles(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.users.view")),
):
    """Get all tenant roles assigned to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Scope check
    if actor.role != "superadmin" and user.tenant_id != actor.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    assignments = (
        db.query(UserTenantRole)
        .filter(UserTenantRole.user_id == user_id)
        .all()
    )

    roles = [
        UserTenantRoleResponse(
            user_id=utr.user_id,
            tenant_role_id=utr.tenant_role_id,
            assigned_at=utr.assigned_at,
            role_name=utr.tenant_role.name if utr.tenant_role else "?",
            role_is_active=utr.tenant_role.is_active if utr.tenant_role else False,
        )
        for utr in assignments
    ]

    return UserRolesResponse(user_id=user_id, roles=roles)


@router.put("/users/{user_id}/roles", response_model=UserRolesResponse)
def set_user_roles(
    user_id: UUID,
    body: UserRoleAssign,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.edit")),
):
    """
    Replace all tenant role assignments for a user.
    All provided tenant_role_ids must belong to the same tenant as the user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if actor.role != "superadmin" and user.tenant_id != actor.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    # Validate all role IDs belong to the user's tenant
    roles = db.query(TenantRole).filter(
        TenantRole.id.in_([str(rid) for rid in body.tenant_role_ids]),
        TenantRole.tenant_id == user.tenant_id,
        TenantRole.is_active == True,  # noqa: E712
    ).all()

    if len(roles) != len(body.tenant_role_ids):
        raise HTTPException(
            status_code=400,
            detail="Uno o más role_ids no son válidos, no pertenecen al tenant del usuario, o están inactivos.",
        )

    # Replace assignments
    db.query(UserTenantRole).filter(UserTenantRole.user_id == user_id).delete(
        synchronize_session="fetch"
    )
    for role in roles:
        db.add(UserTenantRole(
            user_id=user_id,
            tenant_role_id=role.id,
            assigned_by_id=actor.id,
        ))

    db.commit()

    # Invalidate Redis cache for this user
    invalidate_user_permissions_cache(user_id)

    log_event(
        db,
        action="user.roles.set",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=user.tenant_id,
        resource_type="user",
        resource_id=str(user_id),
        detail={
            "assigned_role_ids": [str(rid) for rid in body.tenant_role_ids],
            "assigned_role_names": [r.name for r in roles],
        },
        ip_address=request.client.host if request.client else None,
    )

    # Return updated assignments
    assignments = db.query(UserTenantRole).filter(UserTenantRole.user_id == user_id).all()
    result_roles = [
        UserTenantRoleResponse(
            user_id=utr.user_id,
            tenant_role_id=utr.tenant_role_id,
            assigned_at=utr.assigned_at,
            role_name=utr.tenant_role.name if utr.tenant_role else "?",
            role_is_active=utr.tenant_role.is_active if utr.tenant_role else False,
        )
        for utr in assignments
    ]
    return UserRolesResponse(user_id=user_id, roles=result_roles)


@router.delete("/users/{user_id}/roles/{role_id}", response_model=MessageResponse)
def remove_user_role(
    user_id: UUID,
    role_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.edit")),
):
    """Remove a single role from a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if actor.role != "superadmin" and user.tenant_id != actor.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    assignment = db.query(UserTenantRole).filter(
        UserTenantRole.user_id == user_id,
        UserTenantRole.tenant_role_id == role_id,
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada.")

    role_name = assignment.tenant_role.name if assignment.tenant_role else str(role_id)
    db.delete(assignment)
    db.commit()

    invalidate_user_permissions_cache(user_id)

    log_event(
        db,
        action="user.role.remove",
        user_id=actor.id,
        actor_email=actor.email,
        tenant_id=user.tenant_id,
        resource_type="user",
        resource_id=str(user_id),
        detail={"removed_role_id": str(role_id), "removed_role_name": role_name},
        ip_address=request.client.host if request.client else None,
    )

    return MessageResponse(message=f"Rol '{role_name}' removido del usuario.")
