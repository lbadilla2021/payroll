"""Agrega maestro de clasificaciones LRE

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-11
"""

from alembic import op
from sqlalchemy import text

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS nomina.clasificacion_lre (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(50) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            es_activo   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        );

        CREATE INDEX IF NOT EXISTS ix_clasificacion_lre_tenant
            ON nomina.clasificacion_lre(tenant_id);

        ALTER TABLE nomina.clasificacion_lre ENABLE ROW LEVEL SECURITY;

        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'nomina'
                  AND tablename = 'clasificacion_lre'
                  AND policyname = 'rls_clasificacion_lre_tenant'
            ) THEN
                CREATE POLICY rls_clasificacion_lre_tenant
                    ON nomina.clasificacion_lre
                    USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE));
            END IF;
        END $$;
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("""
        DROP POLICY IF EXISTS rls_clasificacion_lre_tenant ON nomina.clasificacion_lre;
        DROP TABLE IF EXISTS nomina.clasificacion_lre;
    """))
