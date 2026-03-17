from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuthAuditLog


def _log(
    db: Session,
    *,
    request: Request,
    event_type: str,
    outcome: str,
    reason: str | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    email_input: str | None = None,
) -> None:
    db.add(
        AuthAuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            email_input=email_input.lower() if email_input else None,
            event_type=event_type,
            outcome=outcome,
            reason=reason,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
        )
    )


def login_success(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None, email_input: str | None = None) -> None:
    _log(db, request=request, event_type='login_success', outcome='success', tenant_id=tenant_id, user_id=user_id, email_input=email_input)


def login_failure(db: Session, *, request: Request, reason: str, tenant_id: int | None = None, user_id: int | None = None, email_input: str | None = None) -> None:
    _log(db, request=request, event_type='login_failure', outcome='failure', reason=reason, tenant_id=tenant_id, user_id=user_id, email_input=email_input)


def forgot_password_requested(db: Session, *, request: Request, tenant_id: int | None, email_input: str | None) -> None:
    _log(db, request=request, event_type='forgot_password_requested', outcome='accepted', reason='uniform_response', tenant_id=tenant_id, email_input=email_input)


def password_reset_success(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None) -> None:
    _log(db, request=request, event_type='password_reset_success', outcome='success', tenant_id=tenant_id, user_id=user_id)


def password_change_success(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None) -> None:
    _log(db, request=request, event_type='password_change_success', outcome='success', tenant_id=tenant_id, user_id=user_id)


def refresh_success(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None) -> None:
    _log(db, request=request, event_type='refresh_success', outcome='success', tenant_id=tenant_id, user_id=user_id)


def logout(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None) -> None:
    _log(db, request=request, event_type='logout', outcome='success', tenant_id=tenant_id, user_id=user_id)


def logout_all(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None) -> None:
    _log(db, request=request, event_type='logout_all', outcome='success', tenant_id=tenant_id, user_id=user_id)


def session_revoked(db: Session, *, request: Request, tenant_id: int | None, user_id: int | None, reason: str) -> None:
    _log(db, request=request, event_type='session_revoked', outcome='success', tenant_id=tenant_id, user_id=user_id, reason=reason)
