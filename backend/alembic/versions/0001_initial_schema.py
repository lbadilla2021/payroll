"""Initial schema: tenants, users, refresh_tokens, password_reset_tokens, audit_logs

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tenants
    op.create_table('tenants',
        sa.Column('id',            UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name',          sa.String(200), nullable=False),
        sa.Column('slug',          sa.String(100), nullable=False),
        sa.Column('is_active',     sa.Boolean,  nullable=False, server_default='true'),
        sa.Column('max_users',     sa.Integer,  nullable=False, server_default='5'),
        sa.Column('plan',          sa.String(50), nullable=False, server_default='basic'),
        sa.Column('contact_email', sa.String(254)),
        sa.Column('contact_phone', sa.String(30)),
        sa.Column('legal_name',    sa.String(300)),
        sa.Column('tax_id',        sa.String(50)),
        sa.Column('address',       sa.Text),
        sa.Column('notes',         sa.Text),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_tenants_slug',      'tenants', ['slug'], unique=True)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])

    # users
    op.create_table('users',
        sa.Column('id',                    UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id',             UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('email',                 sa.String(254), nullable=False),
        sa.Column('username',              sa.String(100)),
        sa.Column('first_name',            sa.String(100), nullable=False),
        sa.Column('last_name',             sa.String(100), nullable=False),
        sa.Column('password_hash',         sa.String(255), nullable=False),
        sa.Column('role',                  sa.String(50), nullable=False, server_default='viewer'),
        sa.Column('is_active',             sa.Boolean, nullable=False, server_default='true'),
        sa.Column('email_verified',        sa.Boolean, nullable=False, server_default='false'),
        sa.Column('force_password_change', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('phone',                 sa.String(30)),
        sa.Column('job_title',             sa.String(150)),
        sa.Column('last_login_at',         sa.DateTime(timezone=True)),
        sa.Column('last_login_ip',         sa.String(45)),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until',          sa.DateTime(timezone=True)),
        sa.Column('created_at',            sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',            sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_email',     'users', ['email'],    unique=True)
    op.create_index('ix_users_username',  'users', ['username'], unique=True)
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_role',      'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # refresh_tokens
    op.create_table('refresh_tokens',
        sa.Column('id',         UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id',    UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('user_agent', sa.String(512)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_rt_user_id',    'refresh_tokens', ['user_id'])
    op.create_index('ix_rt_token_hash', 'refresh_tokens', ['token_hash'], unique=True)

    # password_reset_tokens
    op.create_table('password_reset_tokens',
        sa.Column('id',         UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id',    UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used',    sa.Boolean, nullable=False, server_default='false'),
        sa.Column('used_at',    sa.DateTime(timezone=True)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_prt_user_id',    'password_reset_tokens', ['user_id'])
    op.create_index('ix_prt_token_hash', 'password_reset_tokens', ['token_hash'], unique=True)

    # audit_logs
    op.create_table('audit_logs',
        sa.Column('id',            UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id',     UUID(as_uuid=True)),
        sa.Column('user_id',       UUID(as_uuid=True)),
        sa.Column('actor_email',   sa.String(254)),
        sa.Column('action',        sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id',   sa.String(100)),
        sa.Column('outcome',       sa.String(20), nullable=False, server_default='success'),
        sa.Column('detail',        sa.Text),
        sa.Column('ip_address',    sa.String(45)),
        sa.Column('user_agent',    sa.String(512)),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_audit_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_user_id',   'audit_logs', ['user_id'])
    op.create_index('ix_audit_action',    'audit_logs', ['action'])
    op.create_index('ix_audit_created',   'audit_logs', ['created_at'])

    # PostgreSQL updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = now(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    for tbl in ('tenants', 'users'):
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        """)


def downgrade() -> None:
    for tbl in ('tenants', 'users'):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl};")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at();")
    op.drop_table('audit_logs')
    op.drop_table('password_reset_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('tenants')
