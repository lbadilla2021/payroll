"""
Invitations endpoint.

Flujo:
  1. Admin/Superadmin llama POST /invitations  → genera token, envía email
  2. El invitado recibe email → hace click → llega a /accept-invitation.html?token=...
  3. Frontend llama GET  /invitations/verify?token=... → valida y retorna datos del invite
  4. Frontend llama POST /invitations/accept → crea la cuenta con su propia contraseña
  5. Frontend redirige a login
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_superadmin
from app.core.config import settings
from app.db.session import get_db
from app.email.service import send_invitation_email
from app.models.models import InvitationToken, Tenant, User
from app.schemas.schemas import (
    InvitationAccept, InvitationCreate, InvitationListResponse,
    InvitationResponse, MessageResponse, UserResponse,
)
from app.services.audit import log_event
from app.core.security import hash_password, validate_password_strength

router = APIRouter(prefix="/invitations", tags=["invitations"])

INVITATION_TTL_HOURS = 72


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_invitation_or_404(db: Session, token: str) -> InvitationToken:
    token_hash = _hash_token(token)
    inv = db.query(InvitationToken).filter(
        InvitationToken.token_hash == token_hash
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no encontrada.")
    return inv


# ── POST /invitations — crear invitación ──────────────────────────────────────

@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    body: InvitationCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    # Permission check
    if actor.role == "viewer":
        raise HTTPException(status_code=403, detail="Sin permisos para invitar usuarios.")

    # Determine target tenant
    if actor.role == "superadmin":
        tenant_id = body.tenant_id
    else:
        tenant_id = actor.tenant_id  # admin can only invite to their own tenant

    # Validate tenant exists and is active
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active == True).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado o inactivo.")
    else:
        if body.invited_role != "superadmin":
            raise HTTPException(status_code=400, detail="Se requiere tenant_id para roles no-superadmin.")
        tenant = None

    # Superadmin role can only be assigned by superadmin
    if body.invited_role == "superadmin" and actor.role != "superadmin":
        raise HTTPException(status_code=403, detail="Solo un superadmin puede invitar a otro superadmin.")

    # Check if email already has a user account
    existing_user = db.query(User).filter(User.email == body.invited_email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo.")

    # Revoke any previous pending invitations for this email+tenant
    db.query(InvitationToken).filter(
        InvitationToken.invited_email == body.invited_email,
        InvitationToken.tenant_id == tenant_id,
        InvitationToken.is_accepted == False,
        InvitationToken.is_revoked == False,
    ).update({"is_revoked": True})

    # Check quota before creating invitation
    if tenant_id:
        active_users = db.query(User).filter(
            User.tenant_id == tenant_id, User.is_active == True
        ).count()
        pending_invites = db.query(InvitationToken).filter(
            InvitationToken.tenant_id == tenant_id,
            InvitationToken.is_accepted == False,
            InvitationToken.is_revoked == False,
            InvitationToken.expires_at > datetime.now(timezone.utc),
        ).count()
        if active_users + pending_invites >= tenant.max_users:
            raise HTTPException(
                status_code=409,
                detail=f"El tenant ha alcanzado su límite de {tenant.max_users} usuarios."
            )

    # Generate token
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITATION_TTL_HOURS)

    inv = InvitationToken(
        tenant_id=tenant_id,
        invited_by_id=actor.id,
        invited_email=body.invited_email,
        invited_role=body.invited_role,
        token_hash=token_hash,
        first_name=body.first_name,
        last_name=body.last_name,
        job_title=body.job_title,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    # Send email
    accept_link = f"{settings.FRONTEND_URL}/accept-invitation.html?token={raw_token}"
    tenant_name = tenant.name if tenant else settings.APP_NAME
    send_invitation_email(
        to_email=body.invited_email,
        invited_by_name=actor.full_name,
        tenant_name=tenant_name,
        accept_link=accept_link,
        role=body.invited_role,
        expires_hours=INVITATION_TTL_HOURS,
    )

    log_event(db, actor, "invitation.created", "invitation", str(inv.id),
              detail=f"Invited {body.invited_email} as {body.invited_role}")

    return inv


# ── GET /invitations/verify — validar token (público, para el frontend) ───────

@router.get("/verify", response_model=InvitationResponse)
def verify_invitation(token: str = Query(...), db: Session = Depends(get_db)):
    inv = _get_invitation_or_404(db, token)

    if inv.is_revoked:
        raise HTTPException(status_code=410, detail="Esta invitación ha sido revocada.")
    if inv.is_accepted:
        raise HTTPException(status_code=410, detail="Esta invitación ya fue aceptada.")
    if inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Esta invitación ha expirado.")

    return inv


# ── POST /invitations/accept — aceptar invitación y crear cuenta ──────────────

@router.post("/accept", response_model=UserResponse)
def accept_invitation(
    body: InvitationAccept,
    request: Request,
    db: Session = Depends(get_db),
):
    inv = _get_invitation_or_404(db, body.token)

    # Validate token state
    if inv.is_revoked:
        raise HTTPException(status_code=410, detail="Esta invitación ha sido revocada.")
    if inv.is_accepted:
        raise HTTPException(status_code=410, detail="Esta invitación ya fue aceptada.")
    if inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Esta invitación ha expirado.")

    # Check email not taken (race condition guard)
    if db.query(User).filter(User.email == inv.invited_email).first():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo.")

    # Validate password strength
    is_valid, pwd_error = validate_password_strength(body.password)
    if not is_valid:
        raise HTTPException(status_code=422, detail=pwd_error)

    # Create user
    user = User(
        tenant_id=inv.tenant_id,
        email=inv.invited_email,
        first_name=body.first_name,
        last_name=body.last_name,
        password_hash=hash_password(body.password),
        role=inv.invited_role,
        is_active=True,
        email_verified=True,  # verified via invitation link
        force_password_change=False,
        job_title=inv.job_title,
    )
    db.add(user)

    # Mark invitation as accepted
    inv.is_accepted = True
    inv.accepted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    log_event(db, user, "invitation.accepted", "user", str(user.id),
              detail=f"Account created via invitation {inv.id}")

    return user


# ── GET /invitations — listar invitaciones del tenant ────────────────────────

@router.get("", response_model=InvitationListResponse)
def list_invitations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tenant_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role == "viewer":
        raise HTTPException(status_code=403, detail="Sin permisos.")

    q = db.query(InvitationToken)

    if actor.role == "superadmin":
        if tenant_id:
            q = q.filter(InvitationToken.tenant_id == tenant_id)
    else:
        q = q.filter(InvitationToken.tenant_id == actor.tenant_id)

    total = q.count()
    items = q.order_by(InvitationToken.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return InvitationListResponse(items=items, total=total, page=page, size=size)


# ── DELETE /invitations/{id} — revocar invitación ────────────────────────────

@router.delete("/{invitation_id}", response_model=MessageResponse)
def revoke_invitation(
    invitation_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role == "viewer":
        raise HTTPException(status_code=403, detail="Sin permisos.")

    inv = db.query(InvitationToken).filter(InvitationToken.id == invitation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no encontrada.")

    # Scope check
    if actor.role != "superadmin" and inv.tenant_id != actor.tenant_id:
        raise HTTPException(status_code=403, detail="Sin permisos.")

    if inv.is_accepted:
        raise HTTPException(status_code=409, detail="No se puede revocar una invitación ya aceptada.")

    inv.is_revoked = True
    db.commit()

    log_event(db, actor, "invitation.revoked", "invitation", str(inv.id))
    return {"message": "Invitación revocada."}