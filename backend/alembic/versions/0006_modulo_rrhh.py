"""Módulo RRHH: schema rrhh.* con todas sus tablas y RLS

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-24

Estrategia: idempotente — cada CREATE TABLE verifica existencia previa.
El schema rrhh ya fue creado en 0005 (junto con nomina).

Tablas creadas (schema rrhh):
  tipo_permiso_global, tipo_cargo_rrhh_global   (catálogos globales)
  supervisor, tipo_permiso                       (por tenant)
  atributo_eval_cuantitativa, evaluacion_cuantitativa
  atributo_eval_cualitativa, evaluacion_cualitativa
  trabajador                                     (tabla central)
  trabajador_apv, trabajador_conyuge_afiliado
  carga_familiar, carga_familiar_sueldo_mensual
  ficha_vacacion, ficha_permiso, ficha_prestamo
  cargo_desempenado, observacion
  trabajador_eval_cuantitativa, trabajador_eval_cualitativa
  contrato_rrhh
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (iguales a 0005)
# ─────────────────────────────────────────────────────────────────────────────

def _table_exists(conn, schema: str, table: str) -> bool:
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = :s AND table_name = :t)"
    ), {"s": schema, "t": table})
    return result.scalar()


def _index_exists(conn, schema: str, index: str) -> bool:
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes "
        "WHERE schemaname = :s AND indexname = :i)"
    ), {"s": schema, "i": index})
    return result.scalar()


def _create_table_if_not_exists(conn, schema: str, table: str, ddl: str):
    if not _table_exists(conn, schema, table):
        conn.execute(text(ddl))


def _create_index_if_not_exists(conn, schema: str, index: str, ddl: str):
    if not _index_exists(conn, schema, index):
        conn.execute(text(ddl))


def _enable_rls(conn, schema: str, tabla: str):
    conn.execute(text(f"ALTER TABLE {schema}.{tabla} ENABLE ROW LEVEL SECURITY"))
    policy_name = f"rls_{tabla}_tenant"
    conn.execute(text(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = '{schema}' AND tablename = '{tabla}'
                AND policyname = '{policy_name}'
            ) THEN
                CREATE POLICY {policy_name} ON {schema}.{tabla}
                USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE));
            END IF;
        END $$
    """))


# ─────────────────────────────────────────────────────────────────────────────
# UPGRADE
# ─────────────────────────────────────────────────────────────────────────────

def upgrade() -> None:
    conn = op.get_bind()

    # Schema rrhh ya fue creado en 0005, pero por si acaso:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS rrhh"))

    # ── Supervisor ────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "supervisor", """
        CREATE TABLE rrhh.supervisor (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id  UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo     VARCHAR(20) NOT NULL,
            nombre     VARCHAR(200) NOT NULL,
            es_activo  BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_supervisor_tenant",
        "CREATE INDEX ix_supervisor_tenant ON rrhh.supervisor(tenant_id)")

    # ── Tipo permiso ──────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "tipo_permiso", """
        CREATE TABLE rrhh.tipo_permiso (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(100) NOT NULL,
            es_activo   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Evaluación cuantitativa (catálogo) ────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "evaluacion_cuantitativa", """
        CREATE TABLE rrhh.evaluacion_cuantitativa (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(100) NOT NULL,
            valor_min   NUMERIC(6,2) NOT NULL DEFAULT 0,
            valor_max   NUMERIC(6,2) NOT NULL DEFAULT 100,
            es_activa   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Atributo evaluación cuantitativa ──────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "atributo_eval_cuantitativa", """
        CREATE TABLE rrhh.atributo_eval_cuantitativa (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(30) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            es_activo   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Evaluación cualitativa (catálogo) ─────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "evaluacion_cualitativa", """
        CREATE TABLE rrhh.evaluacion_cualitativa (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(100) NOT NULL,
            es_activa   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Atributo evaluación cualitativa ───────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "atributo_eval_cualitativa", """
        CREATE TABLE rrhh.atributo_eval_cualitativa (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(30) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            es_activo   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Trabajador ────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "trabajador", """
        CREATE TABLE rrhh.trabajador (
            id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id                 UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo                    VARCHAR(20) NOT NULL,
            rut                       VARCHAR(12) NOT NULL,
            nombres                   VARCHAR(100) NOT NULL,
            apellido_paterno          VARCHAR(100) NOT NULL,
            apellido_materno          VARCHAR(100),
            fecha_nacimiento          DATE,
            email                     VARCHAR(254),
            codigo_pais               VARCHAR(5) DEFAULT 'CL',
            telefono                  VARCHAR(30),
            direccion_calle           VARCHAR(200),
            direccion_numero          VARCHAR(20),
            region_id                 SMALLINT REFERENCES nomina.region(id),
            comuna_id                 SMALLINT REFERENCES nomina.comuna(codigo),
            estado_civil              SMALLINT,
            sexo                      VARCHAR(1),
            es_extranjero             BOOLEAN NOT NULL DEFAULT FALSE,
            nacionalidad              VARCHAR(60),
            tipo_sueldo               VARCHAR(1) NOT NULL DEFAULT 'M',
            moneda_id                 INTEGER NOT NULL DEFAULT 1 REFERENCES nomina.tipo_moneda(id),
            monto_sueldo              NUMERIC(12,2) NOT NULL DEFAULT 0,
            horas_semana              NUMERIC(5,2),
            dias_semana               SMALLINT,
            tipo_gratificacion        VARCHAR(20) NOT NULL DEFAULT 'calculada',
            monto_gratificacion       NUMERIC(12,2),
            monto_movilizacion        NUMERIC(10,2) NOT NULL DEFAULT 0,
            monto_colacion            NUMERIC(10,2) NOT NULL DEFAULT 0,
            forma_pago                VARCHAR(1) NOT NULL DEFAULT 'E',
            banco_id                  INTEGER REFERENCES nomina.banco(id),
            nro_cuenta                VARCHAR(30),
            tipo_mov_bancario         SMALLINT REFERENCES nomina.tipo_movimiento_bancario(id),
            impuesto_agricola         BOOLEAN NOT NULL DEFAULT FALSE,
            art61_ley18768            BOOLEAN NOT NULL DEFAULT FALSE,
            pct_asignacion_zona       NUMERIC(5,2) NOT NULL DEFAULT 0,
            incrementa_pct_zona       BOOLEAN NOT NULL DEFAULT FALSE,
            no_calcula_ajuste_sueldo  BOOLEAN NOT NULL DEFAULT FALSE,
            fecha_contrato            DATE,
            profesion                 VARCHAR(100),
            labor                     VARCHAR(200),
            cargo_id                  UUID REFERENCES nomina.cargo(id),
            sucursal_id               UUID REFERENCES nomina.sucursal(id),
            centro_costo_id           UUID REFERENCES nomina.centro_costo(id),
            supervisor_id             UUID REFERENCES rrhh.supervisor(id),
            tipo_contrato_id          UUID REFERENCES nomina.tipo_contrato(id),
            regimen_previsional       SMALLINT NOT NULL DEFAULT 1,
            afp_id                    INTEGER REFERENCES nomina.afp(id),
            cotizacion_voluntaria_afp NUMERIC(12,2) NOT NULL DEFAULT 0,
            rebaja_imp_cotiz_vol      BOOLEAN NOT NULL DEFAULT FALSE,
            regimen_salud             VARCHAR(10) NOT NULL DEFAULT 'FONASA',
            isapre_id                 INTEGER REFERENCES nomina.isapre(id),
            modalidad_isapre          SMALLINT,
            monto_isapre_pesos        NUMERIC(12,2) NOT NULL DEFAULT 0,
            monto_isapre_uf           NUMERIC(8,4) NOT NULL DEFAULT 0,
            tiene_seg_cesantia        BOOLEAN NOT NULL DEFAULT TRUE,
            contrato_plazo_fijo       BOOLEAN NOT NULL DEFAULT FALSE,
            fecha_ingreso_sc          DATE,
            fecha_ultimo_mes_sc       DATE,
            afp_seg_cesantia_id       INTEGER REFERENCES nomina.afp(id),
            no_cotiza_sis             BOOLEAN NOT NULL DEFAULT FALSE,
            beneficiarios_ges         SMALLINT NOT NULL DEFAULT 0,
            vigencia_ges              SMALLINT,
            tiene_serv_med_cchc       BOOLEAN NOT NULL DEFAULT FALSE,
            tipo_trabajador           SMALLINT NOT NULL DEFAULT 1,
            es_activo                 BOOLEAN NOT NULL DEFAULT TRUE,
            created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, rut),
            UNIQUE (tenant_id, codigo)
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_trabajador_tenant",
        "CREATE INDEX ix_trabajador_tenant ON rrhh.trabajador(tenant_id)")
    _create_index_if_not_exists(conn, "rrhh", "ix_trabajador_rut",
        "CREATE INDEX ix_trabajador_rut ON rrhh.trabajador(tenant_id, rut)")
    _create_index_if_not_exists(conn, "rrhh", "ix_trabajador_activo",
        "CREATE INDEX ix_trabajador_activo ON rrhh.trabajador(tenant_id, es_activo)")
    _create_index_if_not_exists(conn, "rrhh", "ix_trabajador_cargo",
        "CREATE INDEX ix_trabajador_cargo ON rrhh.trabajador(cargo_id)")
    _create_index_if_not_exists(conn, "rrhh", "ix_trabajador_sucursal",
        "CREATE INDEX ix_trabajador_sucursal ON rrhh.trabajador(sucursal_id)")
    _create_index_if_not_exists(conn, "rrhh", "ix_trabajador_cc",
        "CREATE INDEX ix_trabajador_cc ON rrhh.trabajador(centro_costo_id)")

    # ── APV trabajador ────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "trabajador_apv", """
        CREATE TABLE rrhh.trabajador_apv (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id     UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            tipo_apv          VARCHAR(10) NOT NULL,
            moneda_trabajador VARCHAR(5) NOT NULL DEFAULT 'CLP',
            monto_trabajador  NUMERIC(12,4) NOT NULL DEFAULT 0,
            moneda_empleador  VARCHAR(5),
            monto_empleador   NUMERIC(12,4) NOT NULL DEFAULT 0,
            administra_afp    BOOLEAN NOT NULL DEFAULT TRUE,
            afp_id            INTEGER REFERENCES nomina.afp(id),
            otra_institucion  VARCHAR(100),
            rebaja_art42bis   BOOLEAN NOT NULL DEFAULT FALSE,
            fecha_inicio      DATE NOT NULL,
            fecha_termino     DATE,
            es_activo         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_apv_trabajador",
        "CREATE INDEX ix_apv_trabajador ON rrhh.trabajador_apv(trabajador_id)")

    # ── Cónyuge afiliado ──────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "trabajador_conyuge_afiliado", """
        CREATE TABLE rrhh.trabajador_conyuge_afiliado (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id           UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            rut_conyuge             VARCHAR(12) NOT NULL,
            nombres                 VARCHAR(200) NOT NULL,
            afp_id                  INTEGER REFERENCES nomina.afp(id),
            monto_cotiz_voluntaria  NUMERIC(12,2) NOT NULL DEFAULT 0,
            monto_deposito_ahorro   NUMERIC(12,2) NOT NULL DEFAULT 0,
            fecha_inicio            DATE NOT NULL,
            fecha_termino           DATE,
            cesar_cotizacion        BOOLEAN NOT NULL DEFAULT FALSE,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, trabajador_id)
        )
    """)

    # ── Carga familiar ────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "carga_familiar", """
        CREATE TABLE rrhh.carga_familiar (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id     UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            rut               VARCHAR(12) NOT NULL,
            nombres           VARCHAR(200) NOT NULL,
            fecha_nacimiento  DATE NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            tipo_carga        VARCHAR(10) NOT NULL,
            parentesco        VARCHAR(15) NOT NULL,
            es_activa         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_carga_familiar_trabajador",
        "CREATE INDEX ix_carga_familiar_trabajador ON rrhh.carga_familiar(trabajador_id)")
    _create_index_if_not_exists(conn, "rrhh", "ix_carga_familiar_tenant",
        "CREATE INDEX ix_carga_familiar_tenant ON rrhh.carga_familiar(tenant_id)")

    # ── Carga familiar sueldo mensual ─────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "carga_familiar_sueldo_mensual", """
        CREATE TABLE rrhh.carga_familiar_sueldo_mensual (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            anio          SMALLINT NOT NULL,
            mes           SMALLINT NOT NULL,
            sueldo        NUMERIC(12,2) NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, trabajador_id, anio, mes)
        )
    """)

    # ── Ficha vacación ────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "ficha_vacacion", """
        CREATE TABLE rrhh.ficha_vacacion (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id   UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evento    DATE NOT NULL,
            descripcion     VARCHAR(200),
            fecha_desde     DATE NOT NULL,
            fecha_hasta     DATE NOT NULL,
            dias_otorgados  NUMERIC(5,2) NOT NULL DEFAULT 0,
            dias_utilizados NUMERIC(5,2) NOT NULL DEFAULT 0,
            es_progresiva   BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_ficha_vacacion_trabajador",
        "CREATE INDEX ix_ficha_vacacion_trabajador ON rrhh.ficha_vacacion(trabajador_id)")

    # ── Ficha permiso ─────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "ficha_permiso", """
        CREATE TABLE rrhh.ficha_permiso (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id   UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evento    DATE NOT NULL,
            tipo_permiso_id UUID NOT NULL REFERENCES rrhh.tipo_permiso(id),
            fecha_desde     DATE NOT NULL,
            fecha_hasta     DATE NOT NULL,
            dias_otorgados  NUMERIC(5,2) NOT NULL DEFAULT 0,
            observaciones   TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_ficha_permiso_trabajador",
        "CREATE INDEX ix_ficha_permiso_trabajador ON rrhh.ficha_permiso(trabajador_id)")

    # ── Ficha préstamo (RRHH) ─────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "ficha_prestamo", """
        CREATE TABLE rrhh.ficha_prestamo (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id  UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evento   DATE NOT NULL,
            monto          NUMERIC(12,2) NOT NULL DEFAULT 0,
            descripcion    TEXT,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "rrhh", "ix_ficha_prestamo_trabajador",
        "CREATE INDEX ix_ficha_prestamo_trabajador ON rrhh.ficha_prestamo(trabajador_id)")

    # ── Cargo desempeñado ─────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "cargo_desempenado", """
        CREATE TABLE rrhh.cargo_desempenado (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id     UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            cargo_id          UUID REFERENCES nomina.cargo(id),
            cargo_descripcion VARCHAR(100),
            fecha_desde       DATE NOT NULL,
            fecha_hasta       DATE,
            observaciones     TEXT,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Observación ───────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "observacion", """
        CREATE TABLE rrhh.observacion (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evento  DATE NOT NULL,
            supervisor_id UUID REFERENCES rrhh.supervisor(id),
            tipo          VARCHAR(50),
            descripcion   TEXT NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Eval cuantitativa del trabajador ──────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "trabajador_eval_cuantitativa", """
        CREATE TABLE rrhh.trabajador_eval_cuantitativa (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id    UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evaluacion DATE NOT NULL,
            evaluacion_id    UUID NOT NULL REFERENCES rrhh.evaluacion_cuantitativa(id),
            atributo_id      UUID NOT NULL REFERENCES rrhh.atributo_eval_cuantitativa(id),
            valor            NUMERIC(6,2) NOT NULL,
            observaciones    TEXT,
            creado_por_id    UUID REFERENCES users(id),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Eval cualitativa del trabajador ───────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "trabajador_eval_cualitativa", """
        CREATE TABLE rrhh.trabajador_eval_cualitativa (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id    UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evaluacion DATE NOT NULL,
            evaluacion_id    UUID NOT NULL REFERENCES rrhh.evaluacion_cualitativa(id),
            atributo_id      UUID NOT NULL REFERENCES rrhh.atributo_eval_cualitativa(id),
            descripcion      TEXT,
            creado_por_id    UUID REFERENCES users(id),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Contrato RRHH (vista histórica) ───────────────────────────────────────
    _create_table_if_not_exists(conn, "rrhh", "contrato_rrhh", """
        CREATE TABLE rrhh.contrato_rrhh (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id UUID NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
            fecha_evento  DATE NOT NULL,
            supervisor_id UUID REFERENCES rrhh.supervisor(id),
            contrato_id   UUID,
            descripcion   TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── RLS en todas las tablas ───────────────────────────────────────────────
    tablas_rls = [
        "supervisor", "tipo_permiso",
        "evaluacion_cuantitativa", "atributo_eval_cuantitativa",
        "evaluacion_cualitativa", "atributo_eval_cualitativa",
        "trabajador", "trabajador_apv", "trabajador_conyuge_afiliado",
        "carga_familiar", "carga_familiar_sueldo_mensual",
        "ficha_vacacion", "ficha_permiso", "ficha_prestamo",
        "cargo_desempenado", "observacion",
        "trabajador_eval_cuantitativa", "trabajador_eval_cualitativa",
        "contrato_rrhh",
    ]
    for tabla in tablas_rls:
        _enable_rls(conn, "rrhh", tabla)


def downgrade() -> None:
    conn = op.get_bind()
    tablas = [
        "contrato_rrhh",
        "trabajador_eval_cualitativa", "trabajador_eval_cuantitativa",
        "observacion", "cargo_desempenado",
        "ficha_prestamo", "ficha_permiso", "ficha_vacacion",
        "carga_familiar_sueldo_mensual", "carga_familiar",
        "trabajador_conyuge_afiliado", "trabajador_apv",
        "trabajador",
        "atributo_eval_cualitativa", "evaluacion_cualitativa",
        "atributo_eval_cuantitativa", "evaluacion_cuantitativa",
        "tipo_permiso", "supervisor",
    ]
    for t in tablas:
        conn.execute(text(f"DROP TABLE IF EXISTS rrhh.{t} CASCADE"))
    conn.execute(text("DROP SCHEMA IF EXISTS rrhh CASCADE"))
