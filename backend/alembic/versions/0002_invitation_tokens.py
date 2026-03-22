"""Add invitation_tokens table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'invitation_tokens',
        sa.Column('id',            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id',     postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id',   ondelete='SET NULL'), nullable=True),
        sa.Column('invited_email', sa.String(254), nullable=False),
        sa.Column('invited_role',  sa.String(50),  nullable=False, server_default='viewer'),
        sa.Column('token_hash',    sa.String(255), nullable=False, unique=True),
        sa.Column('first_name',    sa.String(100), nullable=True),
        sa.Column('last_name',     sa.String(100), nullable=True),
        sa.Column('job_title',     sa.String(150), nullable=True),
        sa.Column('expires_at',    sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at',   sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_accepted',   sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_revoked',    sa.Boolean, nullable=False, server_default='false'),
        sa.Column('ip_address',    sa.String(45), nullable=True),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_invitation_tokens_tenant_id',     'invitation_tokens', ['tenant_id'])
    op.create_index('ix_invitation_tokens_token_hash',    'invitation_tokens', ['token_hash'])
    op.create_index('ix_invitation_tokens_invited_email', 'invitation_tokens', ['invited_email'])


def downgrade() -> None:
    op.drop_table('invitation_tokens')
