"""RRHH Mantenedores: tablas globales estado_civil, tipo_trabajador, regimen_previsional

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-26
"""

from alembic import op
from sqlalchemy import text

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def _table_exists(conn, schema: str, table: str) -> bool:
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = :s AND table_name = :t)"
    ), {"s": schema, "t": table})
    return result.scalar()


def upgrade():
    conn = op.get_bind()

    if not _table_exists(conn, "rrhh", "estado_civil_global"):
        conn.execute(text("""
            CREATE TABLE rrhh.estado_civil_global (
                id          SMALLSERIAL PRIMARY KEY,
                codigo      SMALLINT    NOT NULL UNIQUE,
                descripcion VARCHAR(100) NOT NULL,
                referencia  VARCHAR(200),
                es_activo   BOOLEAN     NOT NULL DEFAULT TRUE
            )
        """))
        conn.execute(text("""
            INSERT INTO rrhh.estado_civil_global (codigo, descripcion, referencia) VALUES
            (1, 'Soltero/a',                  'Código Civil'),
            (2, 'Casado/a',                   'Código Civil'),
            (3, 'Viudo/a',                    'Código Civil'),
            (4, 'Separado/a judicialmente',   'Ley 19.947 (Matrimonio Civil)'),
            (5, 'Conviviente civil',           'Ley 20.830 (AUC)'),
            (6, 'Divorciado/a',               'Ley 19.947 (Matrimonio Civil)')
        """))

    if not _table_exists(conn, "rrhh", "tipo_trabajador_global"):
        conn.execute(text("""
            CREATE TABLE rrhh.tipo_trabajador_global (
                id          SMALLSERIAL PRIMARY KEY,
                codigo      SMALLINT    NOT NULL UNIQUE,
                descripcion VARCHAR(100) NOT NULL,
                referencia  VARCHAR(200),
                es_activo   BOOLEAN     NOT NULL DEFAULT TRUE
            )
        """))
        conn.execute(text("""
            INSERT INTO rrhh.tipo_trabajador_global (codigo, descripcion, referencia) VALUES
            (1, 'Empleado',                      'Art. 3 Código del Trabajo'),
            (2, 'Obrero',                         'Art. 3 Código del Trabajo'),
            (3, 'Aprendiz',                       'Art. 78 Código del Trabajo'),
            (4, 'Pensionado activo',              'DL 3.500 Art. 68'),
            (5, 'Trabajador de casa particular',  'Art. 146 Código del Trabajo'),
            (6, 'Trabajador agrícola',            'Art. 87 Código del Trabajo')
        """))

    if not _table_exists(conn, "rrhh", "regimen_previsional_global"):
        conn.execute(text("""
            CREATE TABLE rrhh.regimen_previsional_global (
                id          SMALLSERIAL PRIMARY KEY,
                codigo      SMALLINT    NOT NULL UNIQUE,
                descripcion VARCHAR(100) NOT NULL,
                referencia  VARCHAR(200),
                es_activo   BOOLEAN     NOT NULL DEFAULT TRUE
            )
        """))
        conn.execute(text("""
            INSERT INTO rrhh.regimen_previsional_global (codigo, descripcion, referencia) VALUES
            (1, 'AFP (sistema privado)',             'DL 3.500 de 1980'),
            (2, 'IPS — Ex INP (sistema antiguo)',    'Ley 16.395'),
            (3, 'CAPREDENA (FFAA y Carabineros)',    'DFL 1 de 1968'),
            (4, 'DIPRECA (Policía de Investigaciones)', 'DFL 2 de 1968'),
            (5, 'Imponente voluntario AFP',          'DL 3.500 Art. 88')
        """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS rrhh.regimen_previsional_global"))
    conn.execute(text("DROP TABLE IF EXISTS rrhh.tipo_trabajador_global"))
    conn.execute(text("DROP TABLE IF EXISTS rrhh.estado_civil_global"))
