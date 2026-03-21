import json
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import AuditLog


def log_event(
    db: Session,
    action: str,
    outcome: str = "success",
    user_id: Optional[UUID] = None,
    actor_email: Optional[str] = None,
    tenant_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Non-blocking audit write. Errors are logged but don't fail the request."""
    try:
        entry = AuditLog(
            action=action,
            outcome=outcome,
            user_id=user_id,
            actor_email=actor_email,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            detail=json.dumps(detail) if detail else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        db.rollback()
        # Don't re-raise — auditing should never break business logic
        import logging
        logging.getLogger(__name__).error(f"Audit log failed: {exc}")
