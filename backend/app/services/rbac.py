"""
RBAC Service — Permission resolution, cache management, and catalog seed.

Architecture:
  - Permissions are resolved user → user_tenant_roles → tenant_roles
    → tenant_role_permissions → permissions
  - Result is cached in Redis as a SET with 5-minute TTL (O(1) lookup)
  - Base roles (admin, viewer) get default permissions for backward compatibility
  - superadmin bypasses RBAC entirely (handled in dependency layer)
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.rate_limit import _get_redis
from app.models.models import Permission, Tenant, TenantRole, TenantRolePermission

logger = logging.getLogger(__name__)

# ── Default permissions for legacy roles (backward compatibility) ─────────────

ROLE_DEFAULT_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "platform.users.view",
        "platform.users.create",
        "platform.users.edit",
        "platform.users.invite",
        "platform.roles.view",
        "platform.roles.create",
        "platform.roles.edit",
        "platform.settings.view",
        "platform.audit.view",
    },
    "viewer": {
        "platform.users.view",
    },
}

# ── Permission seed catalog ───────────────────────────────────────────────────

PERMISSION_SEED: list[dict] = [
    # module: platform — tenant management
    {"code": "platform.tenants.view",       "name": "Ver tenants",               "module": "platform", "description": "Listar y ver detalle de tenants"},
    {"code": "platform.tenants.create",     "name": "Crear tenants",             "module": "platform", "description": "Crear nuevos tenants en la plataforma"},
    {"code": "platform.tenants.edit",       "name": "Editar tenants",            "module": "platform", "description": "Modificar datos de tenants existentes"},
    {"code": "platform.tenants.deactivate", "name": "Desactivar tenants",        "module": "platform", "description": "Desactivar tenants y sus usuarios"},
    # platform — user management
    {"code": "platform.users.view",         "name": "Ver usuarios",              "module": "platform", "description": "Listar y ver detalle de usuarios"},
    {"code": "platform.users.create",       "name": "Crear usuarios",            "module": "platform", "description": "Crear nuevos usuarios"},
    {"code": "platform.users.edit",         "name": "Editar usuarios",           "module": "platform", "description": "Modificar datos de usuarios existentes"},
    {"code": "platform.users.deactivate",   "name": "Desactivar usuarios",       "module": "platform", "description": "Desactivar cuentas de usuario"},
    {"code": "platform.users.invite",       "name": "Invitar usuarios",          "module": "platform", "description": "Enviar invitaciones a nuevos usuarios"},
    # platform — role management
    {"code": "platform.roles.view",         "name": "Ver roles",                 "module": "platform", "description": "Listar y ver detalle de roles del tenant"},
    {"code": "platform.roles.create",       "name": "Crear roles",               "module": "platform", "description": "Crear nuevos roles para el tenant"},
    {"code": "platform.roles.edit",         "name": "Editar roles",              "module": "platform", "description": "Modificar roles y sus permisos"},
    {"code": "platform.roles.delete",       "name": "Eliminar roles",            "module": "platform", "description": "Eliminar roles del tenant"},
    # platform — audit and settings
    {"code": "platform.audit.view",         "name": "Ver auditoría",             "module": "platform", "description": "Consultar el registro de auditoría"},
    {"code": "platform.settings.view",      "name": "Ver configuración",         "module": "platform", "description": "Ver configuración del tenant"},
    {"code": "platform.settings.edit",      "name": "Editar configuración",      "module": "platform", "description": "Modificar configuración del tenant"},
    {"code": "platform.billing.view",       "name": "Ver facturación",           "module": "platform", "description": "Consultar datos de facturación"},
    {"code": "platform.billing.edit",       "name": "Editar facturación",        "module": "platform", "description": "Modificar datos de facturación y plan"},
    # module: system — technical permissions
    {"code": "system.api_keys.manage",      "name": "Gestionar API keys",        "module": "system",   "description": "Crear, rotar y revocar API keys"},
    {"code": "system.webhooks.manage",      "name": "Gestionar webhooks",        "module": "system",   "description": "Configurar y gestionar webhooks"},
    {"code": "system.integrations.manage",  "name": "Gestionar integraciones",   "module": "system",   "description": "Configurar integraciones con sistemas externos"},
]


# ── Cache helpers ─────────────────────────────────────────────────────────────

CACHE_TTL = 300  # 5 minutes


def _cache_key(user_id: UUID) -> str:
    return f"perms:{user_id}"


def invalidate_user_permissions_cache(user_id: UUID) -> None:
    """Delete the Redis permissions cache for a user. Call after role changes."""
    try:
        r = _get_redis()
        if r:
            r.delete(_cache_key(user_id))
            logger.debug(f"RBAC cache invalidated for user {user_id}")
    except Exception as exc:
        logger.warning(f"RBAC cache invalidation failed for {user_id}: {exc}")


def invalidate_role_users_cache(tenant_role_id: UUID, db: Session) -> None:
    """
    Invalidate cache for ALL users who have a given tenant role.
    Call after role permissions are modified.
    """
    try:
        rows = db.execute(
            text("SELECT user_id FROM user_tenant_roles WHERE tenant_role_id = :rid"),
            {"rid": tenant_role_id},
        ).fetchall()
        for row in rows:
            invalidate_user_permissions_cache(row.user_id)
    except Exception as exc:
        logger.warning(f"RBAC bulk cache invalidation failed for role {tenant_role_id}: {exc}")


# ── Permission resolution ─────────────────────────────────────────────────────

def load_user_permissions(user_id: UUID, user_role: str, db: Session) -> set[str]:
    """
    Load all effective permissions for a user from the database.
    Combines:
      1. Permissions from assigned tenant_roles (RBAC)
      2. Default permissions from legacy role (backward compat)
    """
    try:
        rows = db.execute(
            text("""
                SELECT DISTINCT p.code
                FROM user_tenant_roles utr
                JOIN tenant_role_permissions trp ON trp.tenant_role_id = utr.tenant_role_id
                JOIN tenant_roles tr ON tr.id = utr.tenant_role_id
                JOIN permissions p ON p.id = trp.permission_id
                WHERE utr.user_id = :user_id
                  AND p.is_active = true
                  AND tr.is_active = true
            """),
            {"user_id": str(user_id)},
        ).fetchall()
    except Exception as exc:
        logger.error(f"RBAC DB query failed for user {user_id}: {exc}")
        rows = []

    rbac_perms = {r.code for r in rows}
    base_perms = ROLE_DEFAULT_PERMISSIONS.get(user_role, set())
    return rbac_perms | base_perms


def user_has_permission(user_id: UUID, user_role: str, code: str, db: Session) -> bool:
    """
    Check if a user has a specific permission.
    Uses Redis cache (TTL=5min) for O(1) lookup after first resolution.
    """
    try:
        r = _get_redis()
        if r:
            cache_key = _cache_key(user_id)
            try:
                cached = r.smembers(cache_key)
                if cached:
                    # smembers returns bytes when decode_responses=False, str when True
                    # Our Redis client uses decode_responses=True
                    return code in cached
            except Exception as exc:
                logger.warning(f"RBAC Redis read failed: {exc}")

            # Cache miss — load from DB
            permissions = load_user_permissions(user_id, user_role, db)
            try:
                if permissions:
                    pipe = r.pipeline()
                    pipe.sadd(cache_key, *permissions)
                    pipe.expire(cache_key, CACHE_TTL)
                    pipe.execute()
                else:
                    # Cache empty set with a short TTL sentinel to avoid repeated DB hits
                    r.set(f"{cache_key}:empty", "1", ex=60)
            except Exception as exc:
                logger.warning(f"RBAC Redis write failed: {exc}")

            return code in permissions
    except Exception as exc:
        logger.warning(f"RBAC cache layer failed entirely: {exc}")

    # Fallback: direct DB check without cache
    permissions = load_user_permissions(user_id, user_role, db)
    return code in permissions


# ── Seed ──────────────────────────────────────────────────────────────────────

def seed_permissions(db: Session) -> int:
    """
    Idempotent seed of the permissions catalog.
    Only inserts missing permissions (by code); never updates or deletes.
    Returns the count of newly inserted permissions.
    """
    existing_codes: set[str] = {
        row.code for row in db.query(Permission.code).all()
    }
    inserted = 0
    for entry in PERMISSION_SEED:
        if entry["code"] not in existing_codes:
            db.add(Permission(
                code=entry["code"],
                name=entry["name"],
                description=entry.get("description"),
                module=entry["module"],
                is_active=True,
            ))
            inserted += 1
    if inserted:
        db.commit()
        logger.info(f"RBAC seed: inserted {inserted} new permissions")
    return inserted


def ensure_system_roles_for_tenant(tenant_id: UUID, db: Session) -> None:
    """
    Create system roles (Admin, Viewer) for a tenant if they don't exist yet.
    These are is_system=True and cannot be deleted by the tenant admin.
    """
    system_roles = [
        {"name": "Admin", "description": "Administrador del tenant con acceso completo a gestión"},
        {"name": "Viewer", "description": "Usuario de solo lectura"},
    ]
    existing_names = {
        row.name for row in db.query(TenantRole.name)
        .filter(TenantRole.tenant_id == tenant_id, TenantRole.is_system == True)  # noqa: E712
        .all()
    }
    for role_def in system_roles:
        if role_def["name"] not in existing_names:
            db.add(TenantRole(
                tenant_id=tenant_id,
                name=role_def["name"],
                description=role_def["description"],
                is_system=True,
                is_active=True,
            ))
    db.commit()
