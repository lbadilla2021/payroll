-- =============================================================================
-- MÓDULO: NÓMINA
-- Sistema de Remuneraciones - Payroll
-- Multitenant con RLS (Row-Level Security)
-- Compatible con PostgreSQL 15+
-- =============================================================================
-- Convención: todas las tablas de módulos van en schema "nomina"
--             las tablas de lookup/seed globales NO llevan tenant_id
--             las tablas operacionales SÍ llevan tenant_id + RLS
-- =============================================================================

-- ─── Schema ──────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS nomina;
SET search_path TO nomina, public;

-- =============================================================================
-- TABLAS MAESTRAS GLOBALES (sin tenant_id — son catálogos del sistema)
-- =============================================================================

-- ─── AFP (Administradoras de Fondos de Pensiones) ────────────────────────────
-- Fuente: Tabla equivalencias Previred / Manual Transtecnia cap. 4.4.3
CREATE TABLE nomina.afp (
    id              SERIAL PRIMARY KEY,
    codigo_previred SMALLINT        NOT NULL UNIQUE,  -- código según tabla Previred
    nombre          VARCHAR(100)    NOT NULL,
    nombre_corto    VARCHAR(30)     NOT NULL,
    tasa_trabajador NUMERIC(5,4)    NOT NULL,          -- % cotización obligatoria trabajador
    tasa_sis        NUMERIC(5,4)    NOT NULL DEFAULT 0, -- % SIS (Seguro Invalidez y Sobrevivencia) cargo empleador
    tasa_trabajo_pesado NUMERIC(5,4) NOT NULL DEFAULT 0,
    es_activa       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Seed AFP vigentes Chile 2024 (tasas aproximadas, actualizar según DT)
INSERT INTO nomina.afp (codigo_previred, nombre, nombre_corto, tasa_trabajador, tasa_sis) VALUES
(1,  'AFP Capital',      'Capital',    0.1144, 0.0149),
(2,  'AFP Cuprum',       'Cuprum',     0.1144, 0.0149),
(3,  'AFP Habitat',      'Habitat',    0.1144, 0.0149),
(4,  'AFP Modelo',       'Modelo',     0.1144, 0.0149),
(5,  'AFP Planvital',    'Planvital',  0.1144, 0.0149),
(6,  'AFP ProVida',      'ProVida',    0.1144, 0.0149),
(7,  'AFP Uno',          'Uno',        0.1144, 0.0149),
(8,  'IPS (Ex INP)',     'IPS',        0.0000, 0.0000),
(9,  'EMPART',           'EMPART',     0.0000, 0.0000),
(10, 'SSS (Caja Serv.)', 'SSS',        0.0000, 0.0000);


-- ─── ISAPRE ───────────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.4.3, 7.9.2
CREATE TABLE nomina.isapre (
    id              SERIAL PRIMARY KEY,
    codigo_previred SMALLINT        NOT NULL UNIQUE,
    nombre          VARCHAR(100)    NOT NULL,
    nombre_corto    VARCHAR(30)     NOT NULL,
    es_activa       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

INSERT INTO nomina.isapre (codigo_previred, nombre, nombre_corto) VALUES
(1,  'Fonasa',                        'FONASA'),
(2,  'Isapre Banmédica',              'Banmédica'),
(3,  'Isapre Colmena Golden Cross',   'Colmena'),
(4,  'Isapre Consalud',               'Consalud'),
(5,  'Isapre Cruz Blanca',            'Cruz Blanca'),
(6,  'Isapre Cruz del Norte',         'Cruz del Norte'),
(7,  'Isapre MásSalud',               'MásSalud'),
(8,  'Isapre Óptima',                 'Óptima'),
(9,  'Isapre Vida Tres',              'Vida Tres'),
(10, 'Isapre Esencial',               'Esencial');


-- ─── CCAF (Cajas de Compensación) ────────────────────────────────────────────
-- Fuente: Manual cap. 4.1 (Instituciones Relacionadas), 7.9.3
CREATE TABLE nomina.ccaf (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(10)     NOT NULL UNIQUE,
    nombre          VARCHAR(100)    NOT NULL,
    nombre_corto    VARCHAR(30)     NOT NULL,
    es_activa       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

INSERT INTO nomina.ccaf (codigo, nombre, nombre_corto) VALUES
('001', 'Caja Los Andes',              'Los Andes'),
('002', 'Caja Los Héroes',             'Los Héroes'),
('003', 'Caja La Araucana',            'La Araucana'),
('004', 'Caja 18 de Septiembre',       '18 Sept'),
('005', 'Caja Gabriela Mistral',       'Gabriela Mistral');


-- ─── MUTUALIDADES de Seguridad ────────────────────────────────────────────────
-- Fuente: Manual cap. 4.1 (Instituciones Relacionadas), 7.9.4
CREATE TABLE nomina.mutualidad (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(10)     NOT NULL UNIQUE,
    nombre          VARCHAR(100)    NOT NULL,
    nombre_corto    VARCHAR(30)     NOT NULL,
    tasa_cotizacion NUMERIC(5,4)    NOT NULL DEFAULT 0,  -- tasa básica accidentes trabajo
    es_activa       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

INSERT INTO nomina.mutualidad (codigo, nombre, nombre_corto, tasa_cotizacion) VALUES
('ACHS', 'Asociación Chilena de Seguridad (ACHS)',  'ACHS',    0.0093),
('IST',  'Instituto de Seguridad del Trabajo (IST)', 'IST',     0.0093),
('MUSEG','Mutual de Seguridad CCHC',                 'MutualCC',0.0093),
('INS',  'Instituto de Normalización Previsional (IPS/INS)', 'IPS', 0.0000);


-- ─── BANCOS ───────────────────────────────────────────────────────────────────
-- Fuente: Tabla N°2 manual Transtecnia cap. 9.7.2
CREATE TABLE nomina.banco (
    id      SERIAL PRIMARY KEY,
    codigo  SMALLINT     NOT NULL UNIQUE,  -- código según tabla Transtecnia / Redbanc
    nombre  VARCHAR(100) NOT NULL,
    es_activo BOOLEAN    NOT NULL DEFAULT TRUE
);

INSERT INTO nomina.banco (codigo, nombre) VALUES
(1,   'Banco de Chile'),
(9,   'Banco Internacional'),
(12,  'Banco del Estado de Chile'),
(14,  'Scotiabank Chile'),
(16,  'BCI'),
(27,  'CorpBanca'),
(28,  'Banco BICE'),
(31,  'HSBC Bank (Chile)'),
(37,  'Banco Santander-Chile'),
(39,  'Banco Itaú Chile'),
(41,  'JP Morgan Chase Bank N.A.'),
(43,  'Banco de la Nacion Argentina'),
(45,  'The Bank of Tokyo-Mitsubishi UFJ Ltd.'),
(46,  'The Royal Bank of Scotland (Chile)'),
(49,  'Banco Security'),
(51,  'Banco Falabella'),
(52,  'Deutsche Bank (Chile)'),
(53,  'Banco Ripley'),
(54,  'Rabobank Chile'),
(55,  'Banco Consorcio'),
(56,  'Banco Penta'),
(57,  'Banco Paris'),
(58,  'DnB NOR Bank ASA'),
(504, 'Banco Bilbao Vizcaya Argentaria (BBVA) Chile'),
(672, 'Cooperativa Coopeuch'),
(730, 'Banco Tenpo');


-- ─── TIPO DE MOVIMIENTO BANCARIO ──────────────────────────────────────────────
-- Fuente: Tabla N°3 manual Transtecnia cap. 9.7.2
CREATE TABLE nomina.tipo_movimiento_bancario (
    id          SMALLINT     PRIMARY KEY,
    descripcion VARCHAR(60)  NOT NULL
);

INSERT INTO nomina.tipo_movimiento_bancario (id, descripcion) VALUES
(1, 'Abono Cta. Corriente'),
(2, 'Abono Cta. Vista'),
(3, 'Abono Cta. Ahorro'),
(4, 'Abono Bancuenta Credichile'),
(5, 'Abono Chequera Electrónica Banco Estado'),
(6, 'Abono en Cuenta RUT'),
(7, 'Pago en Efectivo'),
(8, 'Vale Vista por Mesón');


-- ─── REGIONES DE CHILE ────────────────────────────────────────────────────────
CREATE TABLE nomina.region (
    id          SMALLINT     PRIMARY KEY,
    codigo      VARCHAR(5)   NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL,
    es_zona_extrema BOOLEAN  NOT NULL DEFAULT FALSE
);

INSERT INTO nomina.region (id, codigo, nombre, es_zona_extrema) VALUES
(1,  'I',     'Tarapacá',                  TRUE),
(2,  'II',    'Antofagasta',               FALSE),
(3,  'III',   'Atacama',                   FALSE),
(4,  'IV',    'Coquimbo',                  FALSE),
(5,  'V',     'Valparaíso',                FALSE),
(6,  'VI',    'OHiggins',                  FALSE),
(7,  'VII',   'Maule',                     FALSE),
(8,  'VIII',  'Biobío',                    FALSE),
(9,  'IX',    'La Araucanía',              FALSE),
(10, 'X',     'Los Lagos',                 FALSE),
(11, 'XI',    'Aysén',                     TRUE),
(12, 'XII',   'Magallanes',                TRUE),
(13, 'RM',    'Metropolitana',             FALSE),
(14, 'XIV',   'Los Ríos',                  FALSE),
(15, 'XV',    'Arica y Parinacota',        TRUE),
(16, 'XVI',   'Ñuble',                     FALSE);


-- ─── COMUNAS ──────────────────────────────────────────────────────────────────
-- Fuente: Tabla N°1 manual Transtecnia cap. 9.7.2 (extracto representativo)
-- NOTA: se incluye la tabla completa extraída del manual
CREATE TABLE nomina.comuna (
    codigo      SMALLINT     PRIMARY KEY,  -- código Transtecnia/INE
    nombre      VARCHAR(80)  NOT NULL,
    region_id   SMALLINT     NOT NULL REFERENCES nomina.region(id)
);

-- (Muestra representativa; cargar tabla completa desde CSV en producción)
INSERT INTO nomina.comuna (codigo, nombre, region_id) VALUES
-- Región I
(1101,'IQUIQUE',1),(1102,'CAMIÑA',1),(1103,'COLCHANE',1),(1104,'HUARA',1),
(1105,'PICA',1),(1106,'POZO ALMONTE',1),(1107,'ALTO HOSPICIO',1),
(1202,'CAMARONES',1),(1301,'PUTRE',1),(1302,'GENERAL LAGOS',1),
-- Región II
(2101,'ANTOFAGASTA',2),(2102,'MEJILLONES',2),(2103,'SIERRA GORDA',2),
(2104,'TALTAL',2),(2105,'MARIA ELENA',2),(2201,'CALAMA',2),
(2202,'OLLAGUE',2),(2203,'SAN PEDRO DE ATACAMA',2),(2301,'TOCOPILLA',2),
-- Región XIII
(13101,'SANTIAGO',13),(13102,'CERRILLOS',13),(13103,'CERRO NAVIA',13),
(13104,'CONCHALÍ',13),(13105,'EL BOSQUE',13),(13106,'ESTACIÓN CENTRAL',13),
(13107,'HUECHURABA',13),(13108,'INDEPENDENCIA',13),(13109,'LA CISTERNA',13),
(13110,'LA FLORIDA',13),(13111,'LA GRANJA',13),(13112,'LA PINTANA',13),
(13113,'LA REINA',13),(13114,'LAS CONDES',13),(13115,'LO BARNECHEA',13),
(13116,'LO ESPEJO',13),(13117,'LO PRADO',13),(13118,'MACUL',13),
(13119,'MAIPÚ',13),(13120,'ÑUÑOA',13),(13121,'PEDRO AGUIRRE CERDA',13),
(13122,'PEÑALOLÉN',13),(13123,'PROVIDENCIA',13),(13124,'PUDAHUEL',13),
(13125,'QUILICURA',13),(13126,'QUINTA NORMAL',13),(13127,'RECOLETA',13),
(13128,'RENCA',13),(13129,'SAN JOAQUÍN',13),(13130,'SAN MIGUEL',13),
(13131,'SAN RAMÓN',13),(13132,'VITACURA',13),(13201,'PUENTE ALTO',13),
(13202,'PIRQUE',13),(13203,'SAN JOSÉ DE MAIPO',13),(13301,'COLINA',13),
(13302,'LAMPA',13),(13303,'TILTIL',13),(13401,'SAN BERNARDO',13),
(13402,'BUIN',13),(13403,'CALERA DE TANGO',13),(13404,'PAINE',13),
(13501,'MELIPILLA',13),(13502,'ALHUÉ',13),(13503,'CURACAVÍ',13),
(13504,'MARÍA PINTO',13),(13505,'SAN PEDRO',13),(13601,'TALAGANTE',13),
(13602,'EL MONTE',13),(13603,'ISLA DE MAIPO',13),(13604,'PADRE HURTADO',13),
(13605,'PEÑAFLOR',13),
-- Región XV
(15101,'ARICA',15);


-- ─── TIPOS DE MONEDA ─────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.11.2
CREATE TABLE nomina.tipo_moneda (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(10)  NOT NULL UNIQUE,
    descripcion VARCHAR(60)  NOT NULL,
    es_activa   BOOLEAN      NOT NULL DEFAULT TRUE
);

INSERT INTO nomina.tipo_moneda (codigo, descripcion) VALUES
('CLP', 'Peso Chileno'),
('UF',  'Unidad de Fomento'),
('UTM', 'Unidad Tributaria Mensual'),
('USD', 'Dólar Americano'),
('EUR', 'Euro');


-- ─── TRAMOS ASIGNACIÓN FAMILIAR ──────────────────────────────────────────────
-- Fuente: Manual cap. 5.1.2 (se actualiza anualmente por DT)
CREATE TABLE nomina.tramo_asignacion_familiar (
    id              SERIAL PRIMARY KEY,
    anio            SMALLINT     NOT NULL,
    mes             SMALLINT     NOT NULL CHECK (mes BETWEEN 1 AND 12),
    tramo           SMALLINT     NOT NULL CHECK (tramo BETWEEN 1 AND 4),
    renta_desde     NUMERIC(12,2) NOT NULL,
    renta_hasta     NUMERIC(12,2),           -- NULL = sin tope superior (tramo D)
    valor_carga     NUMERIC(10,2) NOT NULL,
    descripcion     VARCHAR(50)  NOT NULL,   -- 'Tramo A','Tramo B','Tramo C','Tramo D'
    UNIQUE (anio, mes, tramo)
);
-- Seed 2024 (valores referenciales — actualizar desde resolución DT)
INSERT INTO nomina.tramo_asignacion_familiar (anio, mes, tramo, renta_desde, renta_hasta, valor_carga, descripcion) VALUES
(2024,1,1,       0, 424510,  14085, 'Tramo A'),
(2024,1,2,  424511, 620250,   9218, 'Tramo B'),
(2024,1,3,  620251, 965700,   2920, 'Tramo C'),
(2024,1,4,  965701,    NULL,     0, 'Tramo D (sin asignación)');
-- (replicar para meses 2..12 o cargar via script de cierre mensual)


-- ─── TRAMOS IMPUESTO ÚNICO 2ª CATEGORÍA (en UTM) ─────────────────────────────
-- Fuente: Manual cap. 5.1.3
CREATE TABLE nomina.tramo_impuesto_unico_utm (
    id              SERIAL PRIMARY KEY,
    anio            SMALLINT      NOT NULL,
    mes             SMALLINT      NOT NULL CHECK (mes BETWEEN 1 AND 12),
    orden           SMALLINT      NOT NULL,
    utm_desde       NUMERIC(8,4)  NOT NULL,
    utm_hasta       NUMERIC(8,4),             -- NULL = sin tope
    tasa            NUMERIC(6,4)  NOT NULL,   -- factor multiplicador (ej. 0.04 = 4%)
    rebaja_utm      NUMERIC(8,4)  NOT NULL DEFAULT 0,
    UNIQUE (anio, mes, orden)
);
-- Seed 2024 tabla UTM (valores referenciales SII — actualizar anualmente)
INSERT INTO nomina.tramo_impuesto_unico_utm (anio, mes, orden, utm_desde, utm_hasta, tasa, rebaja_utm) VALUES
(2024,1,1,  0.0000, 13.5000, 0.0000, 0.0000),
(2024,1,2, 13.5001, 30.0000, 0.0400, 0.5400),
(2024,1,3, 30.0001, 50.0000, 0.0800, 1.7400),
(2024,1,4, 50.0001, 70.0000, 0.1350, 4.4900),
(2024,1,5, 70.0001,120.0000, 0.2300,11.1400),
(2024,1,6,120.0001,150.0000, 0.3040,19.9800),
(2024,1,7,150.0001,310.0000, 0.3550,27.6300),
(2024,1,8,310.0001,   NULL,  0.4000,41.5800);


-- ─── FACTORES UTM / UF / ACTUALIZACIÓN ───────────────────────────────────────
-- Fuente: Manual cap. 4.3
CREATE TABLE nomina.factor_actualizacion (
    id      SERIAL PRIMARY KEY,
    anio    SMALLINT      NOT NULL,
    mes     SMALLINT      NOT NULL CHECK (mes BETWEEN 1 AND 12),
    utm     NUMERIC(12,2) NOT NULL,
    uf      NUMERIC(12,4) NOT NULL,
    factor  NUMERIC(10,6) NOT NULL DEFAULT 1.000000,  -- corrección monetaria
    imm     NUMERIC(12,2) NOT NULL,                   -- Ingreso Mínimo Mensual
    UNIQUE (anio, mes)
);


-- ─── SERVICIO MÉDICO CCHC ─────────────────────────────────────────────────────
-- Fuente: Manual cap. 5.1.5
CREATE TABLE nomina.serv_med_cchc (
    id              SERIAL PRIMARY KEY,
    anio            SMALLINT      NOT NULL,
    mes             SMALLINT      NOT NULL CHECK (mes BETWEEN 1 AND 12),
    porcentaje      NUMERIC(6,4)  NOT NULL,
    tope_uf         NUMERIC(8,4)  NOT NULL,
    valor_carga     NUMERIC(10,2) NOT NULL DEFAULT 0,
    UNIQUE (anio, mes)
);


-- =============================================================================
-- TABLAS OPERACIONALES POR TENANT (con RLS)
-- =============================================================================

-- ─── EMPRESA (parámetros nómina por tenant) ───────────────────────────────────
-- Fuente: Manual cap. 4.1
-- NOTA: la empresa "raíz" ya existe en tabla tenants (public schema).
--       Esta tabla extiende tenant con datos tributarios/previsionales.
CREATE TABLE nomina.empresa_config (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Datos representante legal y contador (cap. 4.1)
    nombre_rep_legal        VARCHAR(200),
    rut_rep_legal           VARCHAR(12),
    nombre_contador         VARCHAR(200),
    rut_contador            VARCHAR(12),
    giro                    VARCHAR(200),

    -- Instituciones relacionadas por defecto (cap. 4.1 sección 2)
    ccaf_id                 INT         REFERENCES nomina.ccaf(id),
    mutualidad_id           INT         REFERENCES nomina.mutualidad(id),

    -- Parámetros de gratificación por defecto
    modalidad_gratificacion VARCHAR(20) NOT NULL DEFAULT 'calculada'
                                CHECK (modalidad_gratificacion IN ('calculada','informada','proporcional','calculada_dict4232','no_paga')),

    -- Logo para liquidaciones
    logo_url                TEXT,

    -- Configuración FUN electrónico
    numero_convenio_fun     VARCHAR(50),

    -- Configuración MAPI (email)
    mapi_nombre_remitente   VARCHAR(100),
    mapi_email_remitente    VARCHAR(254),

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_id)
);

-- RLS
ALTER TABLE nomina.empresa_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY empresa_config_tenant_isolation ON nomina.empresa_config
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── SUCURSALES ───────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.12
CREATE TABLE nomina.sucursal (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo          VARCHAR(20) NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    direccion       VARCHAR(200),
    region_id       SMALLINT    REFERENCES nomina.region(id),
    comuna_id       SMALLINT    REFERENCES nomina.comuna(codigo),
    codigo_pais     VARCHAR(5)  DEFAULT 'CL',
    telefono        VARCHAR(30),
    codigo_previred VARCHAR(20),
    es_activa       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.sucursal ENABLE ROW LEVEL SECURITY;
CREATE POLICY sucursal_tenant_isolation ON nomina.sucursal
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_sucursal_tenant ON nomina.sucursal(tenant_id);


-- ─── CENTROS DE COSTO ────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.5
CREATE TABLE nomina.centro_costo (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo          VARCHAR(20) NOT NULL,
    descripcion     VARCHAR(100) NOT NULL,
    codigo_previred VARCHAR(20),
    es_activo       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.centro_costo ENABLE ROW LEVEL SECURITY;
CREATE POLICY centro_costo_tenant_isolation ON nomina.centro_costo
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_centro_costo_tenant ON nomina.centro_costo(tenant_id);


-- ─── CARGOS ───────────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.6
CREATE TABLE nomina.cargo (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.cargo ENABLE ROW LEVEL SECURITY;
CREATE POLICY cargo_tenant_isolation ON nomina.cargo
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── TIPOS DE CONTRATO ────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.8
CREATE TABLE nomina.tipo_contrato (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.tipo_contrato ENABLE ROW LEVEL SECURITY;
CREATE POLICY tipo_contrato_tenant_isolation ON nomina.tipo_contrato
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── CAUSALES DE FINIQUITO ────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.9
CREATE TABLE nomina.causal_finiquito (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    articulo    VARCHAR(50),   -- artículo Código del Trabajo (ej. "Art. 159 N°1")
    es_activa   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.causal_finiquito ENABLE ROW LEVEL SECURITY;
CREATE POLICY causal_finiquito_tenant_isolation ON nomina.causal_finiquito
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- Seed causales base (Código del Trabajo Chile)
-- Se insertan como sistema al crear tenant, pero aquí las dejamos vacías
-- porque son por tenant. Se cargan en bootstrap.


-- ─── CLÁUSULAS ADICIONALES ───────────────────────────────────────────────────
-- Fuente: Manual cap. 4.10
CREATE TABLE nomina.clausula_adicional (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo          VARCHAR(20) NOT NULL,
    descripcion     VARCHAR(200) NOT NULL,
    texto           TEXT        NOT NULL,
    es_activa       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.clausula_adicional ENABLE ROW LEVEL SECURITY;
CREATE POLICY clausula_adicional_tenant_isolation ON nomina.clausula_adicional
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── HABERES Y DESCUENTOS (conceptos) ────────────────────────────────────────
-- Fuente: Manual cap. 4.7 — extensa descripción de campos
CREATE TABLE nomina.concepto_remuneracion (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo                  VARCHAR(10) NOT NULL,   -- hasta 4 dígitos (puede tener prefijo)
    descripcion             VARCHAR(100) NOT NULL,
    tipo                    VARCHAR(1)  NOT NULL CHECK (tipo IN ('H','D')),  -- Haber / Descuento

    -- Propiedades tributarias/previsionales
    es_imponible            BOOLEAN     NOT NULL DEFAULT TRUE,
    es_tributable           BOOLEAN     NOT NULL DEFAULT TRUE,
    es_renta_exenta         BOOLEAN     NOT NULL DEFAULT FALSE,
    reliquida_impuesto      BOOLEAN     NOT NULL DEFAULT FALSE,  -- rentas accesorias/complementarias

    -- Propiedades de cálculo
    es_fijo                 BOOLEAN     NOT NULL DEFAULT TRUE,   -- FALSE = variable
    es_valor_diario         BOOLEAN     NOT NULL DEFAULT FALSE,
    es_semana_corrida       BOOLEAN     NOT NULL DEFAULT FALSE,
    es_porcentaje           BOOLEAN     NOT NULL DEFAULT FALSE,
    es_adicional_horas_ext  BOOLEAN     NOT NULL DEFAULT FALSE,
    es_horas_extras         BOOLEAN     NOT NULL DEFAULT FALSE,
    adiciona_sueldo_imm     BOOLEAN     NOT NULL DEFAULT FALSE,  -- Ley 20.281 ajuste sueldo base
    es_haber_variable       BOOLEAN     NOT NULL DEFAULT FALSE,  -- para cálculo semana corrida

    -- Descuentos especiales
    es_anticipo             BOOLEAN     NOT NULL DEFAULT FALSE,
    es_prestamo_ccaf        BOOLEAN     NOT NULL DEFAULT FALSE,
    es_prestamo             BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Clasificación Libro de Remuneraciones Electrónico
    clasificacion_lre       VARCHAR(50),
    exportable_lre          BOOLEAN     NOT NULL DEFAULT FALSE,

    es_activo               BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE nomina.concepto_remuneracion ENABLE ROW LEVEL SECURITY;
CREATE POLICY concepto_rem_tenant_isolation ON nomina.concepto_remuneracion
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_concepto_rem_tenant ON nomina.concepto_remuneracion(tenant_id);
CREATE INDEX ix_concepto_rem_tipo   ON nomina.concepto_remuneracion(tenant_id, tipo);


-- ─── PARÁMETROS MENSUALES POR EMPRESA ────────────────────────────────────────
-- Fuente: Manual cap. 5.1.1
CREATE TABLE nomina.parametro_mensual (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    anio            SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),

    -- Valores del período (se toman de tablas globales o ingresan manualmente)
    utm             NUMERIC(12,2) NOT NULL,
    uf              NUMERIC(12,4) NOT NULL,
    imm             NUMERIC(12,2) NOT NULL,    -- Ingreso Mínimo Mensual
    factor_actualizacion NUMERIC(10,6) NOT NULL DEFAULT 1.000000,

    -- Topes imponibles
    tope_imponible_afp   NUMERIC(12,2) NOT NULL,   -- 81.6 UF aprox.
    tope_imponible_salud NUMERIC(12,2) NOT NULL,   -- 60 UF aprox.
    tope_seg_cesantia    NUMERIC(12,2) NOT NULL,

    -- Cotizaciones (pueden sobreescribirse por empresa)
    tasa_acc_trabajo     NUMERIC(6,4) NOT NULL DEFAULT 0.0093,  -- Seguro Acc. Trabajo
    tasa_apv_colectivo   NUMERIC(6,4) NOT NULL DEFAULT 0,

    -- Estado de bloqueo del período
    bloqueado            BOOLEAN      NOT NULL DEFAULT FALSE,
    cerrado              BOOLEAN      NOT NULL DEFAULT FALSE,
    fecha_cierre         TIMESTAMPTZ,

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, anio, mes)
);

ALTER TABLE nomina.parametro_mensual ENABLE ROW LEVEL SECURITY;
CREATE POLICY parametro_mensual_tenant_isolation ON nomina.parametro_mensual
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_param_mensual_tenant_periodo ON nomina.parametro_mensual(tenant_id, anio, mes);


-- ─── MOVIMIENTO MENSUAL (cabecera por trabajador/período) ─────────────────────
-- Fuente: Manual cap. 5.2
CREATE TABLE nomina.movimiento_mensual (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id       UUID        NOT NULL,   -- FK a rrhh.trabajador
    anio                SMALLINT    NOT NULL,
    mes                 SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nro_movimiento      SMALLINT    NOT NULL DEFAULT 1,  -- permite finiquito+recontratación

    -- Situación del mes (cap. 5.2.1)
    dias_ausentes       NUMERIC(5,2) NOT NULL DEFAULT 0,
    dias_no_contratado  NUMERIC(5,2) NOT NULL DEFAULT 0,
    dias_licencia       NUMERIC(5,2) NOT NULL DEFAULT 0,
    dias_movilizacion   NUMERIC(5,2) NOT NULL DEFAULT 0,
    dias_colacion       NUMERIC(5,2) NOT NULL DEFAULT 0,
    dias_vacaciones     NUMERIC(5,2) NOT NULL DEFAULT 0,

    -- Rentas de otro empleador (cap. 5.2.1)
    otras_rentas        NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto_isapre_otro   NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto_salud_iu      NUMERIC(12,2) NOT NULL DEFAULT 0,

    -- Horas extras (cap. 5.2.1)
    hh_extras_normales  NUMERIC(6,2) NOT NULL DEFAULT 0,
    hh_extras_nocturnas NUMERIC(6,2) NOT NULL DEFAULT 0,
    hh_extras_festivas  NUMERIC(6,2) NOT NULL DEFAULT 0,

    -- Cargas retroactivas
    cargas_retroactivas         SMALLINT NOT NULL DEFAULT 0,
    cargas_retro_simples        SMALLINT NOT NULL DEFAULT 0,
    cargas_retro_invalidez      SMALLINT NOT NULL DEFAULT 0,
    cargas_retro_maternales     SMALLINT NOT NULL DEFAULT 0,

    -- Código de movimiento (cap. 5.2.4)
    codigo_movimiento   SMALLINT    NOT NULL DEFAULT 0
        CHECK (codigo_movimiento IN (0,1,2,3,4,5,6,7,8,11)),
    -- 0=Normal,1=Contrato Indefinido,2=Retiro/Despido,3=Subsidio/Licencia,
    -- 4=Permiso s/goce,5=Incorp.Lugar Trabajo,6=Finiquito+Recontratación,
    -- 7=Inicio Serv.Contrato Plazo/Obra,8=Transf.Plazo Fijo/Indef.,11=Ausentismo

    fecha_inicio_mov    DATE,
    fecha_termino_mov   DATE,
    fecha_inicio_licencia DATE,
    fecha_termino_licencia DATE,
    rut_entidad_pagadora VARCHAR(12),  -- para licencias médicas

    imponible_sc_mes_anterior    NUMERIC(12,2) NOT NULL DEFAULT 0,
    imponible_prev_mes_anterior  NUMERIC(12,2) NOT NULL DEFAULT 0,

    -- Resultado del cálculo (se llena tras procesar)
    total_haberes       NUMERIC(12,2),
    total_imponible     NUMERIC(12,2),
    total_tributable    NUMERIC(12,2),
    descuento_afp       NUMERIC(12,2),
    descuento_salud     NUMERIC(12,2),
    impuesto_unico      NUMERIC(12,2),
    total_descuentos    NUMERIC(12,2),
    liquido_pagar       NUMERIC(12,2),
    anticipo            NUMERIC(12,2) NOT NULL DEFAULT 0,

    estado              VARCHAR(20)  NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente','calculado','cerrado')),

    calculado_en        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_id, trabajador_id, anio, mes, nro_movimiento)
);

ALTER TABLE nomina.movimiento_mensual ENABLE ROW LEVEL SECURITY;
CREATE POLICY movimiento_mensual_tenant_isolation ON nomina.movimiento_mensual
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_mov_mensual_tenant_periodo ON nomina.movimiento_mensual(tenant_id, anio, mes);
CREATE INDEX ix_mov_mensual_trabajador     ON nomina.movimiento_mensual(tenant_id, trabajador_id);


-- ─── DETALLE HABERES/DESCUENTOS DEL MOVIMIENTO ────────────────────────────────
-- Fuente: Manual cap. 5.2.2
CREATE TABLE nomina.movimiento_concepto (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    movimiento_id       UUID        NOT NULL REFERENCES nomina.movimiento_mensual(id) ON DELETE CASCADE,
    concepto_id         UUID        NOT NULL REFERENCES nomina.concepto_remuneracion(id),
    tipo                VARCHAR(1)  NOT NULL CHECK (tipo IN ('H','D')),
    valor               NUMERIC(12,2) NOT NULL DEFAULT 0,
    cantidad            NUMERIC(9,4) NOT NULL DEFAULT 1,
    ocurrencia          SMALLINT    NOT NULL DEFAULT 1,
    monto_calculado     NUMERIC(12,2) NOT NULL DEFAULT 0,
    es_semana_corrida   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.movimiento_concepto ENABLE ROW LEVEL SECURITY;
CREATE POLICY movimiento_concepto_tenant_isolation ON nomina.movimiento_concepto
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_mov_concepto_movimiento ON nomina.movimiento_concepto(movimiento_id);
CREATE INDEX ix_mov_concepto_tenant     ON nomina.movimiento_concepto(tenant_id);


-- ─── CONTRATOS ────────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 5.4
CREATE TABLE nomina.contrato (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id       UUID        NOT NULL,   -- FK a rrhh.trabajador
    nro_contrato        VARCHAR(20),
    tipo_contrato_id    UUID        REFERENCES nomina.tipo_contrato(id),
    fecha_inicio        DATE        NOT NULL,
    fecha_termino       DATE,                   -- NULL = indefinido
    cargo_id            UUID        REFERENCES nomina.cargo(id),
    sucursal_id         UUID        REFERENCES nomina.sucursal(id),
    centro_costo_id     UUID        REFERENCES nomina.centro_costo(id),
    labor               VARCHAR(200),
    establecimiento     VARCHAR(200),
    horario_beneficios  VARCHAR(100),
    fecha_emision       DATE,
    observaciones       TEXT,
    estado              VARCHAR(20) NOT NULL DEFAULT 'vigente'
        CHECK (estado IN ('vigente','finiquitado','vencido')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.contrato ENABLE ROW LEVEL SECURITY;
CREATE POLICY contrato_tenant_isolation ON nomina.contrato
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_contrato_tenant      ON nomina.contrato(tenant_id);
CREATE INDEX ix_contrato_trabajador  ON nomina.contrato(tenant_id, trabajador_id);


-- ─── FINIQUITOS ───────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 5.5
CREATE TABLE nomina.finiquito (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id       UUID        NOT NULL,
    movimiento_id       UUID        REFERENCES nomina.movimiento_mensual(id),
    contrato_id         UUID        REFERENCES nomina.contrato(id),
    fecha_inicio        DATE        NOT NULL,
    fecha_finiquito     DATE        NOT NULL,
    cargo_id            UUID        REFERENCES nomina.cargo(id),
    causal_id           UUID        REFERENCES nomina.causal_finiquito(id),
    descripcion_pago    TEXT,
    importa_liquidacion BOOLEAN     NOT NULL DEFAULT FALSE,
    total_finiquito     NUMERIC(12,2),
    estado              VARCHAR(20) NOT NULL DEFAULT 'borrador'
        CHECK (estado IN ('borrador','firmado','pagado')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.finiquito ENABLE ROW LEVEL SECURITY;
CREATE POLICY finiquito_tenant_isolation ON nomina.finiquito
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_finiquito_tenant      ON nomina.finiquito(tenant_id);
CREATE INDEX ix_finiquito_trabajador  ON nomina.finiquito(tenant_id, trabajador_id);


-- ─── CONCEPTOS DE FINIQUITO ───────────────────────────────────────────────────
-- Fuente: Manual cap. 5.5.2
CREATE TABLE nomina.finiquito_concepto (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    finiquito_id    UUID        NOT NULL REFERENCES nomina.finiquito(id) ON DELETE CASCADE,
    descripcion     VARCHAR(200) NOT NULL,
    monto           NUMERIC(12,2) NOT NULL DEFAULT 0,
    es_haber        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.finiquito_concepto ENABLE ROW LEVEL SECURITY;
CREATE POLICY finiquito_concepto_tenant_isolation ON nomina.finiquito_concepto
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── PRÉSTAMOS A TRABAJADORES ────────────────────────────────────────────────
-- Fuente: Manual cap. 8.10
CREATE TABLE nomina.prestamo (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL,
    concepto_id     UUID        NOT NULL REFERENCES nomina.concepto_remuneracion(id),
    monto_total     NUMERIC(12,2) NOT NULL,
    nro_cuotas      SMALLINT    NOT NULL,
    valor_cuota     NUMERIC(12,2) NOT NULL,
    fecha_inicio    DATE        NOT NULL,
    saldo_pendiente NUMERIC(12,2) NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo','cancelado','finiquitado')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.prestamo ENABLE ROW LEVEL SECURITY;
CREATE POLICY prestamo_tenant_isolation ON nomina.prestamo
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_prestamo_tenant     ON nomina.prestamo(tenant_id);
CREATE INDEX ix_prestamo_trabajador ON nomina.prestamo(tenant_id, trabajador_id);


-- ─── CUOTAS DE PRÉSTAMOS ─────────────────────────────────────────────────────
CREATE TABLE nomina.prestamo_cuota (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    prestamo_id     UUID        NOT NULL REFERENCES nomina.prestamo(id) ON DELETE CASCADE,
    nro_cuota       SMALLINT    NOT NULL,
    anio            SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    monto           NUMERIC(12,2) NOT NULL,
    procesar        BOOLEAN     NOT NULL DEFAULT TRUE,
    pagada          BOOLEAN     NOT NULL DEFAULT FALSE,
    fecha_pago      DATE,
    movimiento_id   UUID        REFERENCES nomina.movimiento_mensual(id),
    UNIQUE (prestamo_id, nro_cuota)
);

ALTER TABLE nomina.prestamo_cuota ENABLE ROW LEVEL SECURITY;
CREATE POLICY prestamo_cuota_tenant_isolation ON nomina.prestamo_cuota
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── ANTICIPOS ────────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 6.4, 7.6
CREATE TABLE nomina.anticipo (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL,
    anio            SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    monto           NUMERIC(12,2) NOT NULL,
    fecha_emision   DATE        NOT NULL,
    sucursal_id     UUID        REFERENCES nomina.sucursal(id),
    centro_costo_id UUID        REFERENCES nomina.centro_costo(id),
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente','procesado','anulado')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.anticipo ENABLE ROW LEVEL SECURITY;
CREATE POLICY anticipo_tenant_isolation ON nomina.anticipo
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_anticipo_tenant     ON nomina.anticipo(tenant_id);
CREATE INDEX ix_anticipo_trabajador ON nomina.anticipo(tenant_id, trabajador_id);


-- ─── CERTIFICADOS DE IMPUESTO (DJ 1887) ──────────────────────────────────────
-- Fuente: Manual cap. 6.5
CREATE TABLE nomina.certificado_impuesto (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL,
    anio_comercial  SMALLINT    NOT NULL,
    nro_certificado INT         NOT NULL,
    fecha_emision   DATE        NOT NULL,
    renta_bruta     NUMERIC(12,2) NOT NULL DEFAULT 0,
    renta_imponible NUMERIC(12,2) NOT NULL DEFAULT 0,
    dcto_afp        NUMERIC(12,2) NOT NULL DEFAULT 0,
    dcto_salud      NUMERIC(12,2) NOT NULL DEFAULT 0,
    impuesto_unico  NUMERIC(12,2) NOT NULL DEFAULT 0,
    mayor_retencion NUMERIC(12,2) NOT NULL DEFAULT 0,
    rentas_no_gravadas NUMERIC(12,2) NOT NULL DEFAULT 0,
    rebaja_zona_extrema NUMERIC(12,2) NOT NULL DEFAULT 0,
    rentas_accesorias NUMERIC(12,2) NOT NULL DEFAULT 0,
    tipo_jornada    VARCHAR(1)   CHECK (tipo_jornada IN ('A','B','C','P')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, trabajador_id, anio_comercial)
);

ALTER TABLE nomina.certificado_impuesto ENABLE ROW LEVEL SECURITY;
CREATE POLICY certificado_impuesto_tenant_isolation ON nomina.certificado_impuesto
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── RETENCIONES ANUALES (3% Ley 21.252) ─────────────────────────────────────
-- Fuente: Manual cap. 6.5.6, 7.23
CREATE TABLE nomina.retencion_anual (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL,
    anio            SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    monto           NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, trabajador_id, anio, mes)
);

ALTER TABLE nomina.retencion_anual ENABLE ROW LEVEL SECURITY;
CREATE POLICY retencion_anual_tenant_isolation ON nomina.retencion_anual
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── LIBRO DE REMUNERACIONES ELECTRÓNICO (LRE) ───────────────────────────────
-- Fuente: Manual cap. 7.22
CREATE TABLE nomina.lre_generacion (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    anio            SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    archivo_path    TEXT,
    fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generado_por_id UUID        REFERENCES public.users(id),
    estado          VARCHAR(20) NOT NULL DEFAULT 'generado'
        CHECK (estado IN ('generado','enviado','error')),
    UNIQUE (tenant_id, anio, mes)
);

ALTER TABLE nomina.lre_generacion ENABLE ROW LEVEL SECURITY;
CREATE POLICY lre_generacion_tenant_isolation ON nomina.lre_generacion
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- =============================================================================
-- ÍNDICES ADICIONALES
-- =============================================================================
CREATE INDEX ix_movimiento_mensual_estado ON nomina.movimiento_mensual(tenant_id, estado);
CREATE INDEX ix_prestamo_estado ON nomina.prestamo(tenant_id, estado);

CREATE TABLE nomina.contrato_clausula (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    contrato_id UUID NOT NULL REFERENCES nomina.contrato(id) ON DELETE CASCADE,
    clausula_id UUID NOT NULL REFERENCES nomina.clausula_adicional(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE nomina.contrato_clausula ENABLE ROW LEVEL SECURITY;
CREATE POLICY contrato_clausula_tenant_isolation ON nomina.contrato_clausula
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);