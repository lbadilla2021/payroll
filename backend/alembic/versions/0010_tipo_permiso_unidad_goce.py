"""Agrega columnas unidad y con_goce a rrhh.tipo_permiso

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-10
"""

from alembic import op
from sqlalchemy import text

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE rrhh.tipo_permiso
            ADD COLUMN IF NOT EXISTS unidad   VARCHAR(10) NOT NULL DEFAULT 'dias',
            ADD COLUMN IF NOT EXISTS con_goce BOOLEAN     NOT NULL DEFAULT TRUE;
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE rrhh.tipo_permiso
            DROP COLUMN IF EXISTS unidad,
            DROP COLUMN IF EXISTS con_goce;
    """))
