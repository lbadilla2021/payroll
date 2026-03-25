"""
Groups endpoint.

Groups are named collections of users within a tenant.
Assigning a tenant_role to a group causes all members to inherit its permissions.

Endpoints:
  GET    /groups               — list groups
  POST   /groups               — create group
  GET    /groups/{id}          — get group detail (with members + roles)
  PATCH  /groups/{id}          — update group metadata
  DELETE /groups/{id}          — delete group
  PUT    /groups/{id}/roles    — set roles assigned to group
  GET    /groups/{id}/members  — list members
  PUT    /groups/{id}/members  — set members (replace all)
  POST   /groups/{id}/members/{user_id}   — add single member
  DELETE /groups/{id}/members/{user_id}   — remove single member
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.models.models import (
    Group, GroupMember, GroupRole, TenantRole, User, UserTenantRole,
)
from app.schemas.schemas import (
    GroupCreate, GroupListResponse, GroupMemberResponse,
    GroupResponse, GroupRoleResponse, GroupRolesSet,
    GroupMembersSet, GroupUpdate, MessageResponse,
)
from app.services.audit import log_event
from app.services.rbac import invalidate_user_permissions_cache

router = APIRouter(prefix="/groups", tags=["groups"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_group_or_404(db: Session, group_id: UUID) -> Group:
    g = db.query(Group).filter(Group.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    return g


def _assert_scope(actor: User, group: Group):
    if actor.role != "superadmin" and group.tenant_id != actor.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")


def _build_response(group: Group, db: Session) -> GroupResponse:
    member_count = (
        db.query(sa_func.count(GroupMember.user_id))
        .filter(GroupMember.group_id == group.id)
        .scalar()
    )
    roles = [
        GroupRoleResponse(
            tenant_role_id=gr.tenant_role_id,
            role_name=gr.tenant_role.name if gr.tenant_role else "?",
            role_is_active=gr.tenant_role.is_active if gr.tenant_role else False,
        )
        for gr in group.group_roles
    ]
    return GroupResponse(
        id=group.id,
        tenant_id=group.tenant_id,
        name=group.name,
        description=group.description,
        is_active=group.is_active,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=member_count,
        roles=roles,
    )


def _invalidate_group_members_cache(group_id: UUID, db: Session):
    """Invalidate Redis cache for all members of a group."""
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    for m in members:
        invalidate_user_permissions_cache(m.user_id)


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=GroupListResponse)
def list_groups(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.view")),
):
    q = db.query(Group)
    if actor.role != "superadmin":
        q = q.filter(Group.tenant_id == actor.tenant_id)
    if search:
        q = q.filter(Group.name.ilike(f"%{search}%"))
    if is_active is not None:
        q = q.filter(Group.is_active == is_active)

    total = q.count()
    groups = q.order_by(Group.name).offset((page - 1) * size).limit(size).all()
    for g in groups:
        db.refresh(g)
    return GroupListResponse(
        items=[_build_response(g, db) for g in groups],
        total=total, page=page, size=size,
    )


@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    body: GroupCreate,
    request: Request,
    tenant_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.create")),
):
    # Superadmin must specify tenant_id via query param
    if actor.role == "superadmin":
        target_tenant_id = tenant_id or actor.tenant_id
        if not target_tenant_id:
            raise HTTPException(status_code=400, detail="Superadmin debe especificar tenant_id.")
    else:
        target_tenant_id = actor.tenant_id

    # Duplicate check
    existing = db.query(Group).filter(
        Group.tenant_id == target_tenant_id,
        Group.name == body.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Ya existe un grupo llamado '{body.name}'.")

    group = Group(
        tenant_id=target_tenant_id,
        name=body.name,
        description=body.description,
        is_active=True,
        created_by_id=actor.id,
    )
    db.add(group)
    db.flush()

    # Assign initial roles
    if body.role_ids:
        _set_group_roles(group, body.role_ids, actor.id, db)

    db.commit()
    db.refresh(group)

    log_event(
        db, action="group.create",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=target_tenant_id, resource_type="group",
        resource_id=str(group.id),
        detail={"name": group.name, "role_count": len(body.role_ids)},
        ip_address=request.client.host if request.client else None,
    )
    return _build_response(group, db)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.view")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)
    return _build_response(group, db)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: UUID,
    body: GroupUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.edit")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    if body.name is not None and body.name != group.name:
        dup = db.query(Group).filter(
            Group.tenant_id == group.tenant_id,
            Group.name == body.name,
            Group.id != group_id,
        ).first()
        if dup:
            raise HTTPException(status_code=409, detail=f"Ya existe un grupo llamado '{body.name}'.")
        group.name = body.name

    if body.description is not None:
        group.description = body.description
    if body.is_active is not None:
        group.is_active = body.is_active

    db.commit()
    db.refresh(group)

    if body.is_active is False:
        _invalidate_group_members_cache(group_id, db)

    log_event(
        db, action="group.update",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=group.tenant_id, resource_type="group",
        resource_id=str(group_id),
        detail=body.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    )
    return _build_response(group, db)


@router.delete("/{group_id}", response_model=MessageResponse)
def delete_group(
    group_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.delete")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    _invalidate_group_members_cache(group_id, db)

    name = group.name
    tenant_id = group.tenant_id
    db.delete(group)
    db.commit()

    log_event(
        db, action="group.delete",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=tenant_id, resource_type="group",
        resource_id=str(group_id),
        detail={"name": name},
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message=f"Grupo '{name}' eliminado.")


# ── Group Roles ───────────────────────────────────────────────────────────────

def _set_group_roles(group: Group, role_ids: list[UUID], actor_id: UUID, db: Session):
    """Replace all role assignments for a group (within current session)."""
    valid_roles = db.query(TenantRole).filter(
        TenantRole.id.in_([str(rid) for rid in role_ids]),
        TenantRole.tenant_id == group.tenant_id,
        TenantRole.is_active == True,  # noqa: E712
    ).all()
    if len(valid_roles) != len(role_ids):
        raise HTTPException(
            status_code=400,
            detail="Uno o más role_ids no son válidos, no pertenecen a este tenant, o están inactivos.",
        )
    db.query(GroupRole).filter(GroupRole.group_id == group.id).delete(synchronize_session="fetch")
    for role in valid_roles:
        db.add(GroupRole(group_id=group.id, tenant_role_id=role.id, assigned_by_id=actor_id))


@router.put("/{group_id}/roles", response_model=GroupResponse)
def set_group_roles(
    group_id: UUID,
    body: GroupRolesSet,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.roles.edit")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    _set_group_roles(group, body.tenant_role_ids, actor.id, db)
    db.commit()
    db.refresh(group)

    _invalidate_group_members_cache(group_id, db)

    log_event(
        db, action="group.roles.set",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=group.tenant_id, resource_type="group",
        resource_id=str(group_id),
        detail={"role_count": len(body.tenant_role_ids)},
        ip_address=request.client.host if request.client else None,
    )
    return _build_response(group, db)


# ── Group Members ─────────────────────────────────────────────────────────────

@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def get_group_members(
    group_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.users.view")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    return [
        GroupMemberResponse(
            user_id=m.user_id,
            email=m.user.email if m.user else "?",
            full_name=m.user.full_name if m.user else "?",
            added_at=m.added_at,
        )
        for m in members
    ]


@router.put("/{group_id}/members", response_model=MessageResponse)
def set_group_members(
    group_id: UUID,
    body: GroupMembersSet,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.users.edit")),
):
    """Replace all members of a group. All user_ids must belong to the same tenant."""
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    # Validate users belong to same tenant
    if body.user_ids:
        valid_users = db.query(User).filter(
            User.id.in_([str(uid) for uid in body.user_ids]),
            User.tenant_id == group.tenant_id,
            User.is_active == True,  # noqa: E712
        ).all()
        if len(valid_users) != len(body.user_ids):
            raise HTTPException(
                status_code=400,
                detail="Uno o más user_ids no son válidos, no pertenecen a este tenant, o están inactivos.",
            )

    # Invalidate cache for outgoing members
    _invalidate_group_members_cache(group_id, db)

    # Replace members
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete(synchronize_session="fetch")
    for uid in body.user_ids:
        db.add(GroupMember(group_id=group_id, user_id=uid, added_by_id=actor.id))
    db.commit()

    # Invalidate cache for incoming members
    for uid in body.user_ids:
        invalidate_user_permissions_cache(uid)

    log_event(
        db, action="group.members.set",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=group.tenant_id, resource_type="group",
        resource_id=str(group_id),
        detail={"member_count": len(body.user_ids)},
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message=f"Grupo actualizado con {len(body.user_ids)} miembro(s).")


@router.post("/{group_id}/members/{user_id}", response_model=MessageResponse, status_code=201)
def add_group_member(
    group_id: UUID,
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.users.edit")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    user = db.query(User).filter(User.id == user_id, User.tenant_id == group.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en este tenant.")

    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="El usuario ya es miembro de este grupo.")

    db.add(GroupMember(group_id=group_id, user_id=user_id, added_by_id=actor.id))
    db.commit()

    invalidate_user_permissions_cache(user_id)

    log_event(
        db, action="group.member.add",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=group.tenant_id, resource_type="group",
        resource_id=str(group_id),
        detail={"added_user_id": str(user_id), "added_user_email": user.email},
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message=f"Usuario '{user.email}' agregado al grupo.")


@router.delete("/{group_id}/members/{user_id}", response_model=MessageResponse)
def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("platform.users.edit")),
):
    group = _get_group_or_404(db, group_id)
    _assert_scope(actor, group)

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="El usuario no es miembro de este grupo.")

    user_email = member.user.email if member.user else str(user_id)
    db.delete(member)
    db.commit()

    invalidate_user_permissions_cache(user_id)

    log_event(
        db, action="group.member.remove",
        user_id=actor.id, actor_email=actor.email,
        tenant_id=group.tenant_id, resource_type="group",
        resource_id=str(group_id),
        detail={"removed_user_id": str(user_id), "removed_user_email": user_email},
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message=f"Usuario '{user_email}' removido del grupo.")
