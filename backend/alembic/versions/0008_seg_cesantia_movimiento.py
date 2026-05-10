"""Agrega descuento_seg_cesantia a movimiento_mensual

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-28
"""

from alembic import op
from sqlalchemy import text

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def _column_exists(conn, schema: str, table: str, column: str) -> bool:
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = :s AND table_name = :t AND column_name = :c)"
    ), {"s": schema, "t": table, "c": column})
    return result.scalar()


def upgrade():
    conn = op.get_bind()
    if not _column_exists(conn, "nomina", "movimiento_mensual", "descuento_seg_cesantia"):
        conn.execute(text(
            "ALTER TABLE nomina.movimiento_mensual "
            "ADD COLUMN descuento_seg_cesantia NUMERIC(12,2)"
        ))


def downgrade():
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE nomina.movimiento_mensual "
        "DROP COLUMN IF EXISTS descuento_seg_cesantia"
    ))
