"""Add RBAC tables: permissions, tenant_roles, tenant_role_permissions, user_tenant_roles

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-22

Changes (additive — no existing data is modified):
  - CREATE TABLE permissions
  - CREATE TABLE tenant_roles
  - CREATE TABLE tenant_role_permissions
  - CREATE TABLE user_tenant_roles
  - INSERT permission catalog (21 base permissions)
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


# ── Permission seed data ──────────────────────────────────────────────────────

PERMISSIONS_SEED = [
    # module: platform — tenant management
    ("platform.tenants.view",       "Ver tenants",               "platform", "Listar y ver detalle de tenants"),
    ("platform.tenants.create",     "Crear tenants",             "platform", "Crear nuevos tenants en la plataforma"),
    ("platform.tenants.edit",       "Editar tenants",            "platform", "Modificar datos de tenants existentes"),
    ("platform.tenants.deactivate", "Desactivar tenants",        "platform", "Desactivar tenants y sus usuarios"),
    # platform — user management
    ("platform.users.view",         "Ver usuarios",              "platform", "Listar y ver detalle de usuarios"),
    ("platform.users.create",       "Crear usuarios",            "platform", "Crear nuevos usuarios"),
    ("platform.users.edit",         "Editar usuarios",           "platform", "Modificar datos de usuarios existentes"),
    ("platform.users.deactivate",   "Desactivar usuarios",       "platform", "Desactivar cuentas de usuario"),
    ("platform.users.invite",       "Invitar usuarios",          "platform", "Enviar invitaciones a nuevos usuarios"),
    # platform — role management
    ("platform.roles.view",         "Ver roles",                 "platform", "Listar y ver detalle de roles del tenant"),
    ("platform.roles.create",       "Crear roles",               "platform", "Crear nuevos roles para el tenant"),
    ("platform.roles.edit",         "Editar roles",              "platform", "Modificar roles y sus permisos"),
    ("platform.roles.delete",       "Eliminar roles",            "platform", "Eliminar roles del tenant"),
    # platform — audit and settings
    ("platform.audit.view",         "Ver auditoría",             "platform", "Consultar el registro de auditoría"),
    ("platform.settings.view",      "Ver configuración",         "platform", "Ver configuración del tenant"),
    ("platform.settings.edit",      "Editar configuración",      "platform", "Modificar configuración del tenant"),
    ("platform.billing.view",       "Ver facturación",           "platform", "Consultar datos de facturación"),
    ("platform.billing.edit",       "Editar facturación",        "platform", "Modificar datos de facturación y plan"),
    # module: system — technical permissions
    ("system.api_keys.manage",      "Gestionar API keys",        "system",   "Crear, rotar y revocar API keys"),
    ("system.webhooks.manage",      "Gestionar webhooks",        "system",   "Configurar y gestionar webhooks"),
    ("system.integrations.manage",  "Gestionar integraciones",   "system",   "Configurar integraciones con sistemas externos"),
]


def upgrade() -> None:
    # ── Table: permissions ────────────────────────────────────────────────────
    op.create_table(
        'permissions',
        sa.Column('id',          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code',        sa.String(100), nullable=False, unique=True),
        sa.Column('name',        sa.String(200), nullable=False),
        sa.Column('description', sa.Text,        nullable=True),
        sa.Column('module',      sa.String(100), nullable=False),
        sa.Column('is_active',   sa.Boolean,     nullable=False, server_default='true'),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_permissions_code',      'permissions', ['code'],      unique=True)
    op.create_index('ix_permissions_module',    'permissions', ['module'])
    op.create_index('ix_permissions_is_active', 'permissions', ['is_active'])

    # ── Table: tenant_roles ───────────────────────────────────────────────────
    op.create_table(
        'tenant_roles',
        sa.Column('id',          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id',   postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name',        sa.String(200), nullable=False),
        sa.Column('description', sa.Text,        nullable=True),
        sa.Column('is_active',   sa.Boolean,     nullable=False, server_default='true'),
        sa.Column('is_system',   sa.Boolean,     nullable=False, server_default='false'),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_tenant_roles_tenant_name'),
    )
    op.create_index('ix_tenant_roles_tenant_id', 'tenant_roles', ['tenant_id'])
    op.create_index('ix_tenant_roles_is_active', 'tenant_roles', ['is_active'])

    # ── Table: tenant_role_permissions ────────────────────────────────────────
    op.create_table(
        'tenant_role_permissions',
        sa.Column('tenant_role_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenant_roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id',  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('ix_trp_tenant_role_id', 'tenant_role_permissions', ['tenant_role_id'])
    op.create_index('ix_trp_permission_id',  'tenant_role_permissions', ['permission_id'])

    # ── Table: user_tenant_roles ──────────────────────────────────────────────
    op.create_table(
        'user_tenant_roles',
        sa.Column('user_id',        postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tenant_role_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenant_roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('assigned_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at',    sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_utr_user_id',        'user_tenant_roles', ['user_id'])
    op.create_index('ix_utr_tenant_role_id', 'user_tenant_roles', ['tenant_role_id'])

    # ── Seed permissions catalog ──────────────────────────────────────────────
    permissions_table = sa.table(
        'permissions',
        sa.column('id',          postgresql.UUID(as_uuid=True)),
        sa.column('code',        sa.String),
        sa.column('name',        sa.String),
        sa.column('description', sa.String),
        sa.column('module',      sa.String),
        sa.column('is_active',   sa.Boolean),
    )
    op.bulk_insert(permissions_table, [
        {
            "id": uuid.uuid4(),
            "code": code,
            "name": name,
            "description": description,
            "module": module,
            "is_active": True,
        }
        for code, name, module, description in PERMISSIONS_SEED
    ])


def downgrade() -> None:
    op.drop_table('user_tenant_roles')
    op.drop_table('tenant_role_permissions')
    op.drop_table('tenant_roles')
    op.drop_table('permissions')
