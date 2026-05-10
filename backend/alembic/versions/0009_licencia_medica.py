"""Agrega tabla rrhh.licencia_medica

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-10
"""

from alembic import op
from sqlalchemy import text

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rrhh.licencia_medica (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id   UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_inicio    DATE NOT NULL,
            dias            INTEGER NOT NULL CHECK (dias >= 1),
            fecha_termino   DATE NOT NULL,
            observaciones   TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS ix_licencia_medica_trabajador
            ON rrhh.licencia_medica (trabajador_id);

        CREATE INDEX IF NOT EXISTS ix_licencia_medica_tenant
            ON rrhh.licencia_medica (tenant_id);
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS rrhh.licencia_medica;"))
