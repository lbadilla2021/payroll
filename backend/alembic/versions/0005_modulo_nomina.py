"""Módulo Nómina: schemas nomina.* con todas sus tablas y RLS

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-24

Estrategia: las tablas ya pueden existir (aplicadas manualmente vía schema.sql).
Cada CREATE TABLE y CREATE INDEX se envuelve con verificación EXISTS para ser
idempotente. El downgrade elimina los schemas completos en orden inverso.

Tablas creadas (schema nomina):
  Catálogos globales (sin tenant_id):
    afp, isapre, ccaf, mutualidad, banco, tipo_movimiento_bancario,
    region, comuna, tipo_moneda, tramo_asignacion_familiar,
    tramo_impuesto_unico_utm, factor_actualizacion, serv_med_cchc

  Operacionales por tenant (con RLS):
    empresa_config, sucursal, centro_costo, cargo, tipo_contrato,
    causal_finiquito, clausula_adicional, concepto_remuneracion,
    parametro_mensual, movimiento_mensual, movimiento_concepto,
    contrato, contrato_clausula, finiquito, finiquito_concepto,
    prestamo, prestamo_cuota, anticipo, certificado_impuesto,
    retencion_anual, lre_generacion
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
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


# ─────────────────────────────────────────────────────────────────────────────
# SEEDS
# ─────────────────────────────────────────────────────────────────────────────

AFP_SEED = [
    (1,  1, "AFP Capital",     "Capital",     "0.1144", "0.0149", "0"),
    (2,  2, "AFP Cuprum",      "Cuprum",      "0.1144", "0.0149", "0"),
    (3,  3, "AFP Habitat",     "Habitat",     "0.1144", "0.0149", "0"),
    (4,  4, "AFP Modelo",      "Modelo",      "0.1044", "0.0149", "0"),
    (5,  5, "AFP PlanVital",   "PlanVital",   "0.1116", "0.0149", "0"),
    (6,  6, "AFP ProVida",     "ProVida",     "0.1144", "0.0149", "0"),
    (7,  7, "AFP Uno",         "Uno",         "0.0849", "0.0149", "0"),
    (8,  8, "AFP Confía",      "Confía",      "0.1144", "0.0149", "0"),
    (9, 34, "IPS (ex-INP)",    "IPS",         "0",      "0",      "0"),
    (10,99, "Extranjero NoCot","Extranjero",  "0",      "0",      "0"),
]

ISAPRE_SEED = [
    (1,  1, "FONASA",                         "FONASA",     True),
    (2,  2, "Isapre Banmédica",               "Banmédica",  True),
    (3,  3, "Isapre Consalud",                "Consalud",   True),
    (4,  4, "Isapre Cruz Blanca",             "Cruz Blanca",True),
    (5,  5, "Isapre Cruz del Norte",          "Cruz Norte", True),
    (6,  6, "Isapre Colmena Golden Cross",    "Colmena",    True),
    (7,  7, "Isapre Nueva MasVida",           "MasVida",    True),
    (8,  8, "Isapre Vida Tres",               "Vida Tres",  True),
    (9,  9, "Isapre Esencial",                "Esencial",   True),
    (10,10, "Isapre Chuquicamata",            "Chuquicamata",False),
]


CCAF_SEED = [
    (1, "LOS_ANDES",    "CCAF Los Andes",         "Los Andes",  True),
    (2, "LA_ARAUCANA",  "CCAF La Araucana",        "Araucana",   True),
    (3, "LOS_HEROES",   "CCAF Los Héroes",         "Los Héroes", True),
    (4, "GABRIELA",     "CCAF Gabriela Mistral",   "Gabriela",   True),
    (5, "18_SEPT",      "CCAF 18 de Septiembre",   "18 Sept",    True),
]

MUTUALIDAD_SEED = [
    (1, "ACHS",   "Asociación Chilena de Seguridad",  "ACHS",  "0.0093", True),
    (2, "CChC",   "Mutual de Seguridad CChC",          "CChC",  "0.0093", True),
    (3, "IST",    "Instituto de Seguridad del Trabajo","IST",   "0.0093", True),
    (4, "ISL",    "Instituto de Seguridad Laboral",    "ISL",   "0.0093", True),
]

BANCO_SEED = [
    (1,  1,   "Banco de Chile"),
    (2,  9,   "Banco Internacional"),
    (3,  12,  "Banco del Estado de Chile"),
    (4,  14,  "Scotiabank Chile"),
    (5,  16,  "Banco de Crédito e Inversiones (BCI)"),
    (6,  28,  "Banco Bice"),
    (7,  31,  "HSBC Bank Chile"),
    (8,  37,  "Banco Santander"),
    (9,  39,  "Itaú Corpbanca"),
    (10, 49,  "Banco Security"),
    (11, 51,  "Banco Falabella"),
    (12, 53,  "Banco Ripley"),
    (13, 55,  "Banco Consorcio"),
    (14, 57,  "COOPEUCH"),
    (15, 59,  "Banco BTG Pactual Chile"),
    (16, 60,  "Tapp Caja Los Andes"),
    (17, 61,  "Tenpo Prepago"),
    (18, 62,  "Mercado Pago"),
    (19, 101, "Banco de la Nación Argentina"),
    (20, 104, "Banco do Brasil S.A."),
    (21, 105, "JP Morgan Chase Bank"),
    (22, 106, "Banco de la República Oriental del Uruguay"),
    (23, 110, "The Bank of Tokyo-Mitsubishi UFJ"),
    (24, 112, "Citibank N.A."),
    (25, 504, "BBVA"),
    (26, 507, "Deutsche Bank"),
]

MOV_BANCARIO_SEED = [
    (1, "Depósito en cuenta corriente"),
    (2, "Depósito en cuenta de ahorro"),
    (3, "Depósito en cuenta vista"),
    (4, "Vale vista"),
    (5, "Cheque"),
    (6, "Efectivo"),
    (7, "Tarjeta prepago"),
    (8, "CuentaRUT"),
]

REGION_SEED = [
    (1,  "XV", "Región de Arica y Parinacota",      True),
    (2,  "I",  "Región de Tarapacá",                True),
    (3,  "II", "Región de Antofagasta",              False),
    (4,  "III","Región de Atacama",                  False),
    (5,  "IV", "Región de Coquimbo",                 False),
    (6,  "V",  "Región de Valparaíso",               False),
    (7,  "XIII","Región Metropolitana de Santiago",  False),
    (8,  "VI", "Región del Lib. Gral. B. O'Higgins", False),
    (9,  "VII","Región del Maule",                   False),
    (10, "XVI","Región de Ñuble",                    False),
    (11, "VIII","Región del Biobío",                 False),
    (12, "IX", "Región de La Araucanía",              False),
    (13, "XIV","Región de Los Ríos",                 False),
    (14, "X",  "Región de Los Lagos",                False),
    (15, "XI", "Región de Aysén",                    True),
    (16, "XII","Región de Magallanes y Antártica",   True),
]

MONEDA_SEED = [
    (1, "CLP", "Peso Chileno",          True),
    (2, "UF",  "Unidad de Fomento",     True),
    (3, "UTM", "Unidad Tributaria Mens",True),
    (4, "USD", "Dólar Estadounidense",  True),
    (5, "EUR", "Euro",                  True),
]

# Tramos AF 2024 (valores aproximados — actualizar según Previred)
TRAMO_AF_SEED = [
    # anio, mes, tramo, renta_desde, renta_hasta, valor_carga, descripcion
    (2024, 1, 1,       0,  "358186", "16765", "Tramo A — Sin tope"),
    (2024, 1, 2,  "358187", "540555", "10573", "Tramo B"),
    (2024, 1, 3,  "540556", "770215",     "0", "Tramo C — Sin pago"),
    (2024, 1, 4,  "770216",      None,    "0", "Tramo D — Sin pago"),
]

# Tramos IU 2024 en UTM (tabla SII — valores aproximados)
TRAMO_IU_SEED = [
    # anio, mes, orden, utm_desde, utm_hasta, tasa, rebaja_utm
    (2024, 1, 1, "0",      "13.5",   "0",      "0"),
    (2024, 1, 2, "13.5",   "30",     "0.04",   "0.54"),
    (2024, 1, 3, "30",     "50",     "0.08",   "1.74"),
    (2024, 1, 4, "50",     "70",     "0.135",  "4.49"),
    (2024, 1, 5, "70",     "90",     "0.23",   "11.14"),
    (2024, 1, 6, "90",     "120",    "0.304",  "17.8"),
    (2024, 1, 7, "120",    "150",    "0.355",  "23.9"),
    (2024, 1, 8, "150",    None,     "0.40",   "30.65"),
]


# ─────────────────────────────────────────────────────────────────────────────
# UPGRADE
# ─────────────────────────────────────────────────────────────────────────────

def upgrade() -> None:
    conn = op.get_bind()

    # ── Crear schemas ─────────────────────────────────────────────────────────
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS nomina"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS rrhh"))

    # ── AFP ───────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "afp", """
        CREATE TABLE nomina.afp (
            id                   SERIAL PRIMARY KEY,
            codigo_previred      SMALLINT NOT NULL UNIQUE,
            nombre               VARCHAR(100) NOT NULL,
            nombre_corto         VARCHAR(30) NOT NULL,
            tasa_trabajador      NUMERIC(5,4) NOT NULL,
            tasa_sis             NUMERIC(5,4) NOT NULL DEFAULT 0,
            tasa_trabajo_pesado  NUMERIC(5,4) NOT NULL DEFAULT 0,
            es_activa            BOOLEAN NOT NULL DEFAULT TRUE,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Isapre ────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "isapre", """
        CREATE TABLE nomina.isapre (
            id               SERIAL PRIMARY KEY,
            codigo_previred  SMALLINT NOT NULL UNIQUE,
            nombre           VARCHAR(100) NOT NULL,
            nombre_corto     VARCHAR(30) NOT NULL,
            es_activa        BOOLEAN NOT NULL DEFAULT TRUE,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── CCAF ──────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "ccaf", """
        CREATE TABLE nomina.ccaf (
            id           SERIAL PRIMARY KEY,
            codigo       VARCHAR(10) NOT NULL UNIQUE,
            nombre       VARCHAR(100) NOT NULL,
            nombre_corto VARCHAR(30) NOT NULL,
            es_activa    BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


    # ── Mutualidad ────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "mutualidad", """
        CREATE TABLE nomina.mutualidad (
            id              SERIAL PRIMARY KEY,
            codigo          VARCHAR(50) NOT NULL UNIQUE,
            nombre          VARCHAR(100) NOT NULL,
            nombre_corto    VARCHAR(30) NOT NULL,
            tasa_cotizacion NUMERIC(5,4) NOT NULL DEFAULT 0,
            es_activa       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Banco ─────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "banco", """
        CREATE TABLE nomina.banco (
            id        SERIAL PRIMARY KEY,
            codigo    SMALLINT NOT NULL UNIQUE,
            nombre    VARCHAR(100) NOT NULL,
            es_activo BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)

    # ── Tipo movimiento bancario ───────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "tipo_movimiento_bancario", """
        CREATE TABLE nomina.tipo_movimiento_bancario (
            id          SMALLINT PRIMARY KEY,
            descripcion VARCHAR(60) NOT NULL
        )
    """)

    # ── Región ────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "region", """
        CREATE TABLE nomina.region (
            id              SMALLINT PRIMARY KEY,
            codigo          VARCHAR(5) NOT NULL UNIQUE,
            nombre          VARCHAR(100) NOT NULL,
            es_zona_extrema BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    # ── Comuna ────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "comuna", """
        CREATE TABLE nomina.comuna (
            codigo    SMALLINT PRIMARY KEY,
            nombre    VARCHAR(80) NOT NULL,
            region_id SMALLINT NOT NULL REFERENCES nomina.region(id)
        )
    """)

    # ── Tipo moneda ───────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "tipo_moneda", """
        CREATE TABLE nomina.tipo_moneda (
            id          SERIAL PRIMARY KEY,
            codigo      VARCHAR(10) NOT NULL UNIQUE,
            descripcion VARCHAR(60) NOT NULL,
            es_activa   BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)

    # ── Tramo asignación familiar ──────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "tramo_asignacion_familiar", """
        CREATE TABLE nomina.tramo_asignacion_familiar (
            id          SERIAL PRIMARY KEY,
            anio        SMALLINT NOT NULL,
            mes         SMALLINT NOT NULL,
            tramo       SMALLINT NOT NULL,
            renta_desde NUMERIC(12,2) NOT NULL,
            renta_hasta NUMERIC(12,2),
            valor_carga NUMERIC(10,2) NOT NULL,
            descripcion VARCHAR(50) NOT NULL,
            UNIQUE (anio, mes, tramo)
        )
    """)

    # ── Tramo impuesto único UTM ───────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "tramo_impuesto_unico_utm", """
        CREATE TABLE nomina.tramo_impuesto_unico_utm (
            id         SERIAL PRIMARY KEY,
            anio       SMALLINT NOT NULL,
            mes        SMALLINT NOT NULL,
            orden      SMALLINT NOT NULL,
            utm_desde  NUMERIC(8,4) NOT NULL,
            utm_hasta  NUMERIC(8,4),
            tasa       NUMERIC(6,4) NOT NULL,
            rebaja_utm NUMERIC(8,4) NOT NULL DEFAULT 0,
            UNIQUE (anio, mes, orden)
        )
    """)

    # ── Factor actualización ──────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "factor_actualizacion", """
        CREATE TABLE nomina.factor_actualizacion (
            id     SERIAL PRIMARY KEY,
            anio   SMALLINT NOT NULL,
            mes    SMALLINT NOT NULL,
            utm    NUMERIC(12,2) NOT NULL,
            uf     NUMERIC(12,4) NOT NULL,
            factor NUMERIC(10,6) NOT NULL DEFAULT 1.0,
            imm    NUMERIC(12,2) NOT NULL,
            UNIQUE (anio, mes)
        )
    """)

    # ── Serv. Med. CCHC ───────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "serv_med_cchc", """
        CREATE TABLE nomina.serv_med_cchc (
            id          SERIAL PRIMARY KEY,
            anio        SMALLINT NOT NULL,
            mes         SMALLINT NOT NULL,
            porcentaje  NUMERIC(6,4) NOT NULL,
            tope_uf     NUMERIC(8,4) NOT NULL,
            valor_carga NUMERIC(10,2) NOT NULL DEFAULT 0,
            UNIQUE (anio, mes)
        )
    """)

    # ── Empresa config ────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "empresa_config", """
        CREATE TABLE nomina.empresa_config (
            id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id                UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            nombre_rep_legal         VARCHAR(200),
            rut_rep_legal            VARCHAR(12),
            nombre_contador          VARCHAR(200),
            rut_contador             VARCHAR(12),
            giro                     VARCHAR(200),
            ccaf_id                  INTEGER REFERENCES nomina.ccaf(id),
            mutualidad_id            INTEGER REFERENCES nomina.mutualidad(id),
            modalidad_gratificacion  VARCHAR(20) NOT NULL DEFAULT 'calculada',
            logo_url                 TEXT,
            numero_convenio_fun      VARCHAR(50),
            mapi_nombre_remitente    VARCHAR(100),
            mapi_email_remitente     VARCHAR(254),
            created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_empresa_config_tenant",
        "CREATE INDEX ix_empresa_config_tenant ON nomina.empresa_config(tenant_id)")

    # ── Sucursal ──────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "sucursal", """
        CREATE TABLE nomina.sucursal (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo          VARCHAR(20) NOT NULL,
            nombre          VARCHAR(100) NOT NULL,
            direccion       VARCHAR(200),
            region_id       SMALLINT REFERENCES nomina.region(id),
            comuna_id       SMALLINT REFERENCES nomina.comuna(codigo),
            codigo_pais     VARCHAR(5) DEFAULT 'CL',
            telefono        VARCHAR(30),
            codigo_previred VARCHAR(20),
            es_activa       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_sucursal_tenant",
        "CREATE INDEX ix_sucursal_tenant ON nomina.sucursal(tenant_id)")

    # ── Centro de costo ───────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "centro_costo", """
        CREATE TABLE nomina.centro_costo (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo          VARCHAR(20) NOT NULL,
            descripcion     VARCHAR(100) NOT NULL,
            codigo_previred VARCHAR(20),
            es_activo       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_centro_costo_tenant",
        "CREATE INDEX ix_centro_costo_tenant ON nomina.centro_costo(tenant_id)")

    # ── Cargo ─────────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "cargo", """
        CREATE TABLE nomina.cargo (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(100) NOT NULL,
            es_activo   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_cargo_tenant",
        "CREATE INDEX ix_cargo_tenant ON nomina.cargo(tenant_id)")

    # ── Tipo contrato ─────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "tipo_contrato", """
        CREATE TABLE nomina.tipo_contrato (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(100) NOT NULL,
            es_activo   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Causal finiquito ──────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "causal_finiquito", """
        CREATE TABLE nomina.causal_finiquito (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            articulo    VARCHAR(50),
            es_activa   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Cláusula adicional ────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "clausula_adicional", """
        CREATE TABLE nomina.clausula_adicional (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo      VARCHAR(20) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            texto       TEXT NOT NULL,
            es_activa   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)

    # ── Concepto remuneración ─────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "concepto_remuneracion", """
        CREATE TABLE nomina.concepto_remuneracion (
            id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id              UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            codigo                 VARCHAR(10) NOT NULL,
            descripcion            VARCHAR(100) NOT NULL,
            tipo                   VARCHAR(1) NOT NULL,
            es_imponible           BOOLEAN NOT NULL DEFAULT TRUE,
            es_tributable          BOOLEAN NOT NULL DEFAULT TRUE,
            es_renta_exenta        BOOLEAN NOT NULL DEFAULT FALSE,
            reliquida_impuesto     BOOLEAN NOT NULL DEFAULT FALSE,
            es_fijo                BOOLEAN NOT NULL DEFAULT TRUE,
            es_valor_diario        BOOLEAN NOT NULL DEFAULT FALSE,
            es_semana_corrida      BOOLEAN NOT NULL DEFAULT FALSE,
            es_porcentaje          BOOLEAN NOT NULL DEFAULT FALSE,
            es_adicional_horas_ext BOOLEAN NOT NULL DEFAULT FALSE,
            es_horas_extras        BOOLEAN NOT NULL DEFAULT FALSE,
            adiciona_sueldo_imm    BOOLEAN NOT NULL DEFAULT FALSE,
            es_haber_variable      BOOLEAN NOT NULL DEFAULT FALSE,
            es_anticipo            BOOLEAN NOT NULL DEFAULT FALSE,
            es_prestamo_ccaf       BOOLEAN NOT NULL DEFAULT FALSE,
            es_prestamo            BOOLEAN NOT NULL DEFAULT FALSE,
            clasificacion_lre      VARCHAR(50),
            exportable_lre         BOOLEAN NOT NULL DEFAULT FALSE,
            es_activo              BOOLEAN NOT NULL DEFAULT TRUE,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, codigo)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_concepto_rem_tenant",
        "CREATE INDEX ix_concepto_rem_tenant ON nomina.concepto_remuneracion(tenant_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_concepto_rem_tipo",
        "CREATE INDEX ix_concepto_rem_tipo ON nomina.concepto_remuneracion(tenant_id, tipo)")

    # ── Parámetro mensual ─────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "parametro_mensual", """
        CREATE TABLE nomina.parametro_mensual (
            id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id            UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            anio                 SMALLINT NOT NULL,
            mes                  SMALLINT NOT NULL,
            utm                  NUMERIC(12,2) NOT NULL,
            uf                   NUMERIC(12,4) NOT NULL,
            imm                  NUMERIC(12,2) NOT NULL,
            factor_actualizacion NUMERIC(10,6) NOT NULL DEFAULT 1.0,
            tope_imponible_afp   NUMERIC(12,2) NOT NULL,
            tope_imponible_salud NUMERIC(12,2) NOT NULL,
            tope_seg_cesantia    NUMERIC(12,2) NOT NULL,
            tasa_acc_trabajo     NUMERIC(6,4) NOT NULL DEFAULT 0.0093,
            tasa_apv_colectivo   NUMERIC(6,4) NOT NULL DEFAULT 0,
            bloqueado            BOOLEAN NOT NULL DEFAULT FALSE,
            cerrado              BOOLEAN NOT NULL DEFAULT FALSE,
            fecha_cierre         TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, anio, mes)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_param_mensual_tenant_periodo",
        "CREATE INDEX ix_param_mensual_tenant_periodo ON nomina.parametro_mensual(tenant_id, anio, mes)")

    # ── Movimiento mensual ────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "movimiento_mensual", """
        CREATE TABLE nomina.movimiento_mensual (
            id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id                    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id                UUID NOT NULL,
            anio                         SMALLINT NOT NULL,
            mes                          SMALLINT NOT NULL,
            nro_movimiento               SMALLINT NOT NULL DEFAULT 1,
            dias_ausentes                NUMERIC(5,2) NOT NULL DEFAULT 0,
            dias_no_contratado           NUMERIC(5,2) NOT NULL DEFAULT 0,
            dias_licencia                NUMERIC(5,2) NOT NULL DEFAULT 0,
            dias_movilizacion            NUMERIC(5,2) NOT NULL DEFAULT 0,
            dias_colacion                NUMERIC(5,2) NOT NULL DEFAULT 0,
            dias_vacaciones              NUMERIC(5,2) NOT NULL DEFAULT 0,
            otras_rentas                 NUMERIC(12,2) NOT NULL DEFAULT 0,
            monto_isapre_otro            NUMERIC(12,2) NOT NULL DEFAULT 0,
            monto_salud_iu               NUMERIC(12,2) NOT NULL DEFAULT 0,
            hh_extras_normales           NUMERIC(6,2) NOT NULL DEFAULT 0,
            hh_extras_nocturnas          NUMERIC(6,2) NOT NULL DEFAULT 0,
            hh_extras_festivas           NUMERIC(6,2) NOT NULL DEFAULT 0,
            cargas_retroactivas          SMALLINT NOT NULL DEFAULT 0,
            cargas_retro_simples         SMALLINT NOT NULL DEFAULT 0,
            cargas_retro_invalidez       SMALLINT NOT NULL DEFAULT 0,
            cargas_retro_maternales      SMALLINT NOT NULL DEFAULT 0,
            codigo_movimiento            SMALLINT NOT NULL DEFAULT 0,
            fecha_inicio_mov             DATE,
            fecha_termino_mov            DATE,
            fecha_inicio_licencia        DATE,
            fecha_termino_licencia       DATE,
            rut_entidad_pagadora         VARCHAR(12),
            imponible_sc_mes_anterior    NUMERIC(12,2) NOT NULL DEFAULT 0,
            imponible_prev_mes_anterior  NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_haberes                NUMERIC(12,2),
            total_imponible              NUMERIC(12,2),
            total_tributable             NUMERIC(12,2),
            descuento_afp                NUMERIC(12,2),
            descuento_salud              NUMERIC(12,2),
            impuesto_unico               NUMERIC(12,2),
            total_descuentos             NUMERIC(12,2),
            liquido_pagar                NUMERIC(12,2),
            anticipo                     NUMERIC(12,2) NOT NULL DEFAULT 0,
            estado                       VARCHAR(20) NOT NULL DEFAULT 'pendiente',
            calculado_en                 TIMESTAMPTZ,
            created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, trabajador_id, anio, mes, nro_movimiento)
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_mov_mensual_tenant_periodo",
        "CREATE INDEX ix_mov_mensual_tenant_periodo ON nomina.movimiento_mensual(tenant_id, anio, mes)")
    _create_index_if_not_exists(conn, "nomina", "ix_mov_mensual_trabajador",
        "CREATE INDEX ix_mov_mensual_trabajador ON nomina.movimiento_mensual(tenant_id, trabajador_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_movimiento_mensual_estado",
        "CREATE INDEX ix_movimiento_mensual_estado ON nomina.movimiento_mensual(tenant_id, estado)")

    # ── Movimiento concepto ───────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "movimiento_concepto", """
        CREATE TABLE nomina.movimiento_concepto (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            movimiento_id    UUID NOT NULL REFERENCES nomina.movimiento_mensual(id) ON DELETE CASCADE,
            concepto_id      UUID NOT NULL REFERENCES nomina.concepto_remuneracion(id),
            tipo             VARCHAR(1) NOT NULL,
            valor            NUMERIC(12,2) NOT NULL DEFAULT 0,
            cantidad         NUMERIC(9,4) NOT NULL DEFAULT 1,
            ocurrencia       SMALLINT NOT NULL DEFAULT 1,
            monto_calculado  NUMERIC(12,2) NOT NULL DEFAULT 0,
            es_semana_corrida BOOLEAN NOT NULL DEFAULT FALSE,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_mov_concepto_movimiento",
        "CREATE INDEX ix_mov_concepto_movimiento ON nomina.movimiento_concepto(movimiento_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_mov_concepto_tenant",
        "CREATE INDEX ix_mov_concepto_tenant ON nomina.movimiento_concepto(tenant_id)")

    # ── Contrato ──────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "contrato", """
        CREATE TABLE nomina.contrato (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id      UUID NOT NULL,
            nro_contrato       VARCHAR(20),
            tipo_contrato_id   UUID REFERENCES nomina.tipo_contrato(id),
            fecha_inicio       DATE NOT NULL,
            fecha_termino      DATE,
            cargo_id           UUID REFERENCES nomina.cargo(id),
            sucursal_id        UUID REFERENCES nomina.sucursal(id),
            centro_costo_id    UUID REFERENCES nomina.centro_costo(id),
            labor              VARCHAR(200),
            establecimiento    VARCHAR(200),
            horario_beneficios VARCHAR(100),
            fecha_emision      DATE,
            observaciones      TEXT,
            estado             VARCHAR(20) NOT NULL DEFAULT 'vigente',
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_contrato_tenant",
        "CREATE INDEX ix_contrato_tenant ON nomina.contrato(tenant_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_contrato_trabajador",
        "CREATE INDEX ix_contrato_trabajador ON nomina.contrato(tenant_id, trabajador_id)")

    # ── Contrato cláusula ─────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "contrato_clausula", """
        CREATE TABLE nomina.contrato_clausula (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            contrato_id UUID NOT NULL REFERENCES nomina.contrato(id) ON DELETE CASCADE,
            clausula_id UUID NOT NULL REFERENCES nomina.clausula_adicional(id),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Finiquito ─────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "finiquito", """
        CREATE TABLE nomina.finiquito (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id       UUID NOT NULL,
            movimiento_id       UUID REFERENCES nomina.movimiento_mensual(id),
            contrato_id         UUID REFERENCES nomina.contrato(id),
            fecha_inicio        DATE NOT NULL,
            fecha_finiquito     DATE NOT NULL,
            cargo_id            UUID REFERENCES nomina.cargo(id),
            causal_id           UUID REFERENCES nomina.causal_finiquito(id),
            descripcion_pago    TEXT,
            importa_liquidacion BOOLEAN NOT NULL DEFAULT FALSE,
            total_finiquito     NUMERIC(12,2),
            estado              VARCHAR(20) NOT NULL DEFAULT 'borrador',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_finiquito_tenant",
        "CREATE INDEX ix_finiquito_tenant ON nomina.finiquito(tenant_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_finiquito_trabajador",
        "CREATE INDEX ix_finiquito_trabajador ON nomina.finiquito(tenant_id, trabajador_id)")

    # ── Finiquito concepto ────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "finiquito_concepto", """
        CREATE TABLE nomina.finiquito_concepto (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            finiquito_id UUID NOT NULL REFERENCES nomina.finiquito(id) ON DELETE CASCADE,
            descripcion  VARCHAR(200) NOT NULL,
            monto        NUMERIC(12,2) NOT NULL DEFAULT 0,
            es_haber     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Préstamo ──────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "prestamo", """
        CREATE TABLE nomina.prestamo (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id   UUID NOT NULL,
            concepto_id     UUID NOT NULL REFERENCES nomina.concepto_remuneracion(id),
            monto_total     NUMERIC(12,2) NOT NULL,
            nro_cuotas      SMALLINT NOT NULL,
            valor_cuota     NUMERIC(12,2) NOT NULL,
            fecha_inicio    DATE NOT NULL,
            saldo_pendiente NUMERIC(12,2) NOT NULL,
            estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_prestamo_tenant",
        "CREATE INDEX ix_prestamo_tenant ON nomina.prestamo(tenant_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_prestamo_trabajador",
        "CREATE INDEX ix_prestamo_trabajador ON nomina.prestamo(tenant_id, trabajador_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_prestamo_estado",
        "CREATE INDEX ix_prestamo_estado ON nomina.prestamo(tenant_id, estado)")

    # ── Préstamo cuota ────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "prestamo_cuota", """
        CREATE TABLE nomina.prestamo_cuota (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            prestamo_id   UUID NOT NULL REFERENCES nomina.prestamo(id) ON DELETE CASCADE,
            nro_cuota     SMALLINT NOT NULL,
            anio          SMALLINT NOT NULL,
            mes           SMALLINT NOT NULL,
            monto         NUMERIC(12,2) NOT NULL,
            procesar      BOOLEAN NOT NULL DEFAULT TRUE,
            pagada        BOOLEAN NOT NULL DEFAULT FALSE,
            fecha_pago    DATE,
            movimiento_id UUID REFERENCES nomina.movimiento_mensual(id),
            UNIQUE (prestamo_id, nro_cuota)
        )
    """)

    # ── Anticipo ──────────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "anticipo", """
        CREATE TABLE nomina.anticipo (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id   UUID NOT NULL,
            anio            SMALLINT NOT NULL,
            mes             SMALLINT NOT NULL,
            monto           NUMERIC(12,2) NOT NULL,
            fecha_emision   DATE NOT NULL,
            sucursal_id     UUID REFERENCES nomina.sucursal(id),
            centro_costo_id UUID REFERENCES nomina.centro_costo(id),
            estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    _create_index_if_not_exists(conn, "nomina", "ix_anticipo_tenant",
        "CREATE INDEX ix_anticipo_tenant ON nomina.anticipo(tenant_id)")
    _create_index_if_not_exists(conn, "nomina", "ix_anticipo_trabajador",
        "CREATE INDEX ix_anticipo_trabajador ON nomina.anticipo(tenant_id, trabajador_id)")

    # ── Certificado impuesto ──────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "certificado_impuesto", """
        CREATE TABLE nomina.certificado_impuesto (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id       UUID NOT NULL,
            anio_comercial      SMALLINT NOT NULL,
            nro_certificado     INTEGER NOT NULL,
            fecha_emision       DATE NOT NULL,
            renta_bruta         NUMERIC(12,2) NOT NULL DEFAULT 0,
            renta_imponible     NUMERIC(12,2) NOT NULL DEFAULT 0,
            dcto_afp            NUMERIC(12,2) NOT NULL DEFAULT 0,
            dcto_salud          NUMERIC(12,2) NOT NULL DEFAULT 0,
            impuesto_unico      NUMERIC(12,2) NOT NULL DEFAULT 0,
            mayor_retencion     NUMERIC(12,2) NOT NULL DEFAULT 0,
            rentas_no_gravadas  NUMERIC(12,2) NOT NULL DEFAULT 0,
            rebaja_zona_extrema NUMERIC(12,2) NOT NULL DEFAULT 0,
            rentas_accesorias   NUMERIC(12,2) NOT NULL DEFAULT 0,
            tipo_jornada        VARCHAR(1),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, trabajador_id, anio_comercial)
        )
    """)

    # ── Retención anual ───────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "retencion_anual", """
        CREATE TABLE nomina.retencion_anual (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            trabajador_id UUID NOT NULL,
            anio          SMALLINT NOT NULL,
            mes           SMALLINT NOT NULL,
            monto         NUMERIC(12,2) NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, trabajador_id, anio, mes)
        )
    """)

    # ── LRE generación ────────────────────────────────────────────────────────
    _create_table_if_not_exists(conn, "nomina", "lre_generacion", """
        CREATE TABLE nomina.lre_generacion (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            anio             SMALLINT NOT NULL,
            mes              SMALLINT NOT NULL,
            archivo_path     TEXT,
            fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            generado_por_id  UUID REFERENCES users(id),
            estado           VARCHAR(20) NOT NULL DEFAULT 'generado',
            UNIQUE (tenant_id, anio, mes)
        )
    """)

    # ── RLS en todas las tablas operacionales ─────────────────────────────────
    tablas_rls = [
        "empresa_config", "sucursal", "centro_costo", "cargo",
        "tipo_contrato", "causal_finiquito", "clausula_adicional",
        "concepto_remuneracion", "parametro_mensual", "movimiento_mensual",
        "movimiento_concepto", "contrato", "contrato_clausula",
        "finiquito", "finiquito_concepto", "prestamo", "prestamo_cuota",
        "anticipo", "certificado_impuesto", "retencion_anual", "lre_generacion",
    ]
    for tabla in tablas_rls:
        conn.execute(text(f"ALTER TABLE nomina.{tabla} ENABLE ROW LEVEL SECURITY"))
        policy_name = f"rls_{tabla}_tenant"
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname = 'nomina' AND tablename = '{tabla}'
                    AND policyname = '{policy_name}'
                ) THEN
                    CREATE POLICY {policy_name} ON nomina.{tabla}
                    USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE));
                END IF;
            END $$
        """))

    # ── Seeds catálogos globales ───────────────────────────────────────────────
    # AFP
    for row in AFP_SEED:
        conn.execute(text("""
            INSERT INTO nomina.afp (id, codigo_previred, nombre, nombre_corto,
                tasa_trabajador, tasa_sis, tasa_trabajo_pesado)
            VALUES (:id, :cp, :nom, :nc, :tt, :ts, :tp)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "cp": row[1], "nom": row[2], "nc": row[3],
               "tt": row[4], "ts": row[5], "tp": row[6]})

    # Isapres
    for row in ISAPRE_SEED:
        conn.execute(text("""
            INSERT INTO nomina.isapre (id, codigo_previred, nombre, nombre_corto, es_activa)
            VALUES (:id, :cp, :nom, :nc, :ea)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "cp": row[1], "nom": row[2], "nc": row[3], "ea": row[4]})

    # CCAF
    for row in CCAF_SEED:
        conn.execute(text("""
            INSERT INTO nomina.ccaf (id, codigo, nombre, nombre_corto, es_activa)
            VALUES (:id, :co, :nom, :nc, :ea)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "co": row[1], "nom": row[2], "nc": row[3], "ea": row[4]})

    # Mutualidades
    for row in MUTUALIDAD_SEED:
        conn.execute(text("""
            INSERT INTO nomina.mutualidad (id, codigo, nombre, nombre_corto, tasa_cotizacion, es_activa)
            VALUES (:id, :co, :nom, :nc, :tc, :ea)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "co": row[1], "nom": row[2],
               "nc": row[3], "tc": row[4], "ea": row[5]})

    # Bancos
    for row in BANCO_SEED:
        conn.execute(text("""
            INSERT INTO nomina.banco (id, codigo, nombre)
            VALUES (:id, :co, :nom)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "co": row[1], "nom": row[2]})

    # Mov. bancarios
    for row in MOV_BANCARIO_SEED:
        conn.execute(text("""
            INSERT INTO nomina.tipo_movimiento_bancario (id, descripcion)
            VALUES (:id, :desc)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "desc": row[1]})

    # Regiones
    for row in REGION_SEED:
        conn.execute(text("""
            INSERT INTO nomina.region (id, codigo, nombre, es_zona_extrema)
            VALUES (:id, :co, :nom, :ze)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "co": row[1], "nom": row[2], "ze": row[3]})

    # Monedas
    for row in MONEDA_SEED:
        conn.execute(text("""
            INSERT INTO nomina.tipo_moneda (id, codigo, descripcion, es_activa)
            VALUES (:id, :co, :desc, :ea)
            ON CONFLICT DO NOTHING
        """), {"id": row[0], "co": row[1], "desc": row[2], "ea": row[3]})

    # Tramos AF 2024
    for row in TRAMO_AF_SEED:
        conn.execute(text("""
            INSERT INTO nomina.tramo_asignacion_familiar
                (anio, mes, tramo, renta_desde, renta_hasta, valor_carga, descripcion)
            VALUES (:a, :m, :t, :rd, :rh, :vc, :desc)
            ON CONFLICT DO NOTHING
        """), {"a": row[0], "m": row[1], "t": row[2], "rd": row[3],
               "rh": row[4], "vc": row[5], "desc": row[6]})

    # Tramos IU 2024
    for row in TRAMO_IU_SEED:
        conn.execute(text("""
            INSERT INTO nomina.tramo_impuesto_unico_utm
                (anio, mes, orden, utm_desde, utm_hasta, tasa, rebaja_utm)
            VALUES (:a, :m, :o, :ud, :uh, :t, :r)
            ON CONFLICT DO NOTHING
        """), {"a": row[0], "m": row[1], "o": row[2], "ud": row[3],
               "uh": row[4], "t": row[5], "r": row[6]})


def downgrade() -> None:
    conn = op.get_bind()
    # Eliminar en orden inverso (FK-safe)
    tablas = [
        "lre_generacion", "retencion_anual", "certificado_impuesto",
        "anticipo", "prestamo_cuota", "prestamo",
        "finiquito_concepto", "finiquito",
        "contrato_clausula", "contrato",
        "movimiento_concepto", "movimiento_mensual",
        "parametro_mensual", "concepto_remuneracion",
        "clausula_adicional", "causal_finiquito",
        "tipo_contrato", "cargo", "centro_costo", "sucursal", "empresa_config",
        "serv_med_cchc", "factor_actualizacion",
        "tramo_impuesto_unico_utm", "tramo_asignacion_familiar",
        "tipo_moneda", "comuna", "region",
        "tipo_movimiento_bancario", "banco",
        "mutualidad", "ccaf", "isapre", "afp",
    ]
    for t in tablas:
        conn.execute(text(f"DROP TABLE IF EXISTS nomina.{t} CASCADE"))
    conn.execute(text("DROP SCHEMA IF EXISTS nomina CASCADE"))
