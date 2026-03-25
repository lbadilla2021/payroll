"""Add system roles seed per tenant + groups feature

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-22

Changes:
  - CREATE TABLE groups
  - CREATE TABLE group_members  (user ↔ group)
  - CREATE TABLE group_roles    (group ↔ tenant_role)
  - For every existing tenant: create 4 system roles with their permissions
    · Superadmin  — is_system, all platform.* permissions
    · Admin       — is_system, user/role/settings management (no tenants)
    · User        — is_system, no admin permissions (placeholder for app modules)
    · Viewer      — is_system, view-only permissions
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


# ── System role definitions ───────────────────────────────────────────────────
# Each entry: (name, description, list_of_permission_codes)

SYSTEM_ROLES = [
    (
        "Superadmin",
        "Acceso total a la plataforma sin restricciones",
        [
            "platform.tenants.view", "platform.tenants.create",
            "platform.tenants.edit", "platform.tenants.deactivate",
            "platform.users.view", "platform.users.create",
            "platform.users.edit", "platform.users.deactivate",
            "platform.users.invite",
            "platform.roles.view", "platform.roles.create",
            "platform.roles.edit", "platform.roles.delete",
            "platform.audit.view",
            "platform.settings.view", "platform.settings.edit",
            "platform.billing.view", "platform.billing.edit",
            "system.api_keys.manage", "system.webhooks.manage",
            "system.integrations.manage",
        ],
    ),
    (
        "Admin",
        "Administrador del tenant: gestión de usuarios, roles y configuración",
        [
            "platform.users.view", "platform.users.create",
            "platform.users.edit", "platform.users.deactivate",
            "platform.users.invite",
            "platform.roles.view", "platform.roles.create",
            "platform.roles.edit", "platform.roles.delete",
            "platform.audit.view",
            "platform.settings.view", "platform.settings.edit",
        ],
    ),
    (
        "User",
        "Usuario estándar con acceso operacional (sin administración)",
        [
            "platform.users.view",
            "platform.settings.view",
        ],
    ),
    (
        "Viewer",
        "Solo consulta — sin capacidad de editar ni administrar",
        [
            "platform.users.view",
        ],
    ),
]


def upgrade() -> None:
    # ── Table: groups ─────────────────────────────────────────────────────────
    op.create_table(
        'groups',
        sa.Column('id',          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id',   postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name',        sa.String(200), nullable=False),
        sa.Column('description', sa.Text,        nullable=True),
        sa.Column('is_active',   sa.Boolean,     nullable=False, server_default='true'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),
    )
    op.create_index('ix_groups_tenant_id', 'groups', ['tenant_id'])
    op.create_index('ix_groups_is_active', 'groups', ['is_active'])

    # ── Table: group_members ──────────────────────────────────────────────────
    op.create_table(
        'group_members',
        sa.Column('group_id',      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id',       postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('added_by_id',   postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('added_at',      sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_user_id',  'group_members', ['user_id'])

    # ── Table: group_roles ────────────────────────────────────────────────────
    op.create_table(
        'group_roles',
        sa.Column('group_id',      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tenant_role_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenant_roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('assigned_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at',    sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_group_roles_group_id',      'group_roles', ['group_id'])
    op.create_index('ix_group_roles_tenant_role_id', 'group_roles', ['tenant_role_id'])

    # ── Seed system roles for every existing tenant ───────────────────────────
    conn = op.get_bind()

    # Fetch all permission codes → id mapping
    perm_rows = conn.execute(text("SELECT id, code FROM permissions WHERE is_active = true")).fetchall()
    perm_map = {row.code: row.id for row in perm_rows}

    # Fetch all existing tenants
    tenant_rows = conn.execute(text("SELECT id FROM tenants")).fetchall()

    tenant_roles_rows = []
    trp_rows = []

    for tenant_row in tenant_rows:
        tenant_id = tenant_row.id

        # Check which system roles already exist for this tenant
        existing = {
            row.name for row in conn.execute(
                text("SELECT name FROM tenant_roles WHERE tenant_id = :tid AND is_system = true"),
                {"tid": tenant_id},
            ).fetchall()
        }

        for role_name, role_desc, perm_codes in SYSTEM_ROLES:
            if role_name in existing:
                continue
            role_id = uuid.uuid4()
            tenant_roles_rows.append({
                "id": role_id,
                "tenant_id": tenant_id,
                "name": role_name,
                "description": role_desc,
                "is_active": True,
                "is_system": True,
            })
            for code in perm_codes:
                if code in perm_map:
                    trp_rows.append({
                        "tenant_role_id": role_id,
                        "permission_id": perm_map[code],
                    })

    if tenant_roles_rows:
        conn.execute(
            text("""
                INSERT INTO tenant_roles (id, tenant_id, name, description, is_active, is_system)
                VALUES (:id, :tenant_id, :name, :description, :is_active, :is_system)
            """),
            tenant_roles_rows,
        )
    if trp_rows:
        conn.execute(
            text("""
                INSERT INTO tenant_role_permissions (tenant_role_id, permission_id)
                VALUES (:tenant_role_id, :permission_id)
            """),
            trp_rows,
        )


def downgrade() -> None:
    op.drop_table('group_roles')
    op.drop_table('group_members')
    op.drop_table('groups')
    # Note: system roles are NOT removed on downgrade to avoid data loss
