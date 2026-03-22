"""
Permissions catalog endpoint.

Read-only access to the platform permission catalog.
Used by the frontend to build role-permission assignment UI.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.db.session import get_db
from app.models.models import Permission
from app.schemas.schemas import PermissionListResponse, PermissionResponse

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=PermissionListResponse)
def list_permissions(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=200),
    module: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _actor=Depends(require_permission("platform.roles.view")),
):
    """
    List all active permissions in the catalog.
    Optionally filter by module or search by code/name.
    """
    q = db.query(Permission).filter(Permission.is_active == True)  # noqa: E712

    if module:
        q = q.filter(Permission.module == module)
    if search:
        q = q.filter(
            Permission.code.ilike(f"%{search}%") |
            Permission.name.ilike(f"%{search}%")
        )

    total = q.count()
    items = (
        q.order_by(Permission.module, Permission.code)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return PermissionListResponse(
        items=[PermissionResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
    )
