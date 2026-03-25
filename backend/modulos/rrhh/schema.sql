-- =============================================================================
-- MÓDULO: RRHH (Recursos Humanos)
-- Datos personales y laborales de trabajadores
-- Multitenant con RLS (Row-Level Security)
-- Compatible con PostgreSQL 15+
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS rrhh;
SET search_path TO rrhh, nomina, public;

-- =============================================================================
-- TABLAS MAESTRAS GLOBALES (catálogos sin tenant_id)
-- =============================================================================

-- ─── TIPOS DE PERMISOS ────────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.2
-- NOTA: los tipos base los crea el sistema, pero pueden ser por-tenant
--       → aquí como catálogo global de referencia; extensibles por tenant
CREATE TABLE rrhh.tipo_permiso_global (
    id          SERIAL      PRIMARY KEY,
    codigo      VARCHAR(20) NOT NULL UNIQUE,
    descripcion VARCHAR(100) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE
);

INSERT INTO rrhh.tipo_permiso_global (codigo, descripcion) VALUES
('ADM',  'Administrativo'),
('MED',  'Médico'),
('PERS', 'Personal'),
('SIN',  'Sindical'),
('LIC',  'Licencia Médica'),
('VAC',  'Vacaciones'),
('OTRO', 'Otro');


-- ─── TIPOS DE CARGO (RRHH) ────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.6
-- Catálogo de tipos de cargo para evaluaciones RRHH
CREATE TABLE rrhh.tipo_cargo_rrhh_global (
    id          SERIAL      PRIMARY KEY,
    codigo      VARCHAR(20) NOT NULL UNIQUE,
    descripcion VARCHAR(100) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE
);


-- =============================================================================
-- TABLAS OPERACIONALES POR TENANT
-- =============================================================================

-- ─── SUPERVISORES ────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.1
CREATE TABLE rrhh.supervisor (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    nombre      VARCHAR(200) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.supervisor ENABLE ROW LEVEL SECURITY;
CREATE POLICY supervisor_tenant_isolation ON rrhh.supervisor
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_supervisor_tenant ON rrhh.supervisor(tenant_id);


-- ─── TIPOS DE PERMISOS POR TENANT ─────────────────────────────────────────────
-- Fuente: Manual cap. 8.2 — cada empresa puede tener sus propios tipos
CREATE TABLE rrhh.tipo_permiso (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.tipo_permiso ENABLE ROW LEVEL SECURITY;
CREATE POLICY tipo_permiso_tenant_isolation ON rrhh.tipo_permiso
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── ATRIBUTOS EVALUACIÓN CUANTITATIVA ────────────────────────────────────────
-- Fuente: Manual cap. 8.5
CREATE TABLE rrhh.atributo_eval_cuantitativa (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(30) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.atributo_eval_cuantitativa ENABLE ROW LEVEL SECURITY;
CREATE POLICY atrib_eval_cuan_tenant_isolation ON rrhh.atributo_eval_cuantitativa
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── EVALUACIONES CUANTITATIVAS (escalas) ─────────────────────────────────────
-- Fuente: Manual cap. 8.4
CREATE TABLE rrhh.evaluacion_cuantitativa (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    valor_min   NUMERIC(5,2) NOT NULL DEFAULT 0,
    valor_max   NUMERIC(5,2) NOT NULL DEFAULT 100,
    es_activa   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.evaluacion_cuantitativa ENABLE ROW LEVEL SECURITY;
CREATE POLICY eval_cuantitativa_tenant_isolation ON rrhh.evaluacion_cuantitativa
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── ATRIBUTOS EVALUACIÓN CUALITATIVA ────────────────────────────────────────
-- Fuente: Manual cap. 8.8
CREATE TABLE rrhh.atributo_eval_cualitativa (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(30) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    es_activo   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.atributo_eval_cualitativa ENABLE ROW LEVEL SECURITY;
CREATE POLICY atrib_eval_cual_tenant_isolation ON rrhh.atributo_eval_cualitativa
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── EVALUACIONES CUALITATIVAS (opciones) ────────────────────────────────────
-- Fuente: Manual cap. 8.7
CREATE TABLE rrhh.evaluacion_cualitativa (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo      VARCHAR(20) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    es_activa   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.evaluacion_cualitativa ENABLE ROW LEVEL SECURITY;
CREATE POLICY eval_cualitativa_tenant_isolation ON rrhh.evaluacion_cualitativa
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- =============================================================================
-- TRABAJADOR — tabla central del módulo RRHH
-- =============================================================================

-- ─── TRABAJADOR ───────────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.4, 4.4.1 (Datos Personales), 4.4.2 (Laborales),
--         4.4.3 (Previsionales), 4.4.4 (Cargas Familiares)
CREATE TABLE rrhh.trabajador (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    codigo              VARCHAR(20) NOT NULL,

    -- ── Datos Personales (cap. 4.4.1) ────────────────────────────────────────
    rut                 VARCHAR(12) NOT NULL,      -- con DV, ej. "12345678-9"
    nombres             VARCHAR(100) NOT NULL,
    apellido_paterno    VARCHAR(100) NOT NULL,
    apellido_materno    VARCHAR(100),
    fecha_nacimiento    DATE,
    email               VARCHAR(254),
    codigo_pais         VARCHAR(5)  DEFAULT 'CL',
    telefono            VARCHAR(30),
    direccion_calle     VARCHAR(200),
    direccion_numero    VARCHAR(20),
    region_id           SMALLINT    REFERENCES nomina.region(id),
    comuna_id           SMALLINT    REFERENCES nomina.comuna(codigo),
    -- Adicionales
    estado_civil        SMALLINT    CHECK (estado_civil IN (1,2,3,4)),
        -- 1=Soltero,2=Casado,3=Viudo,4=Separado
    sexo                VARCHAR(1)  CHECK (sexo IN ('M','F')),
    es_extranjero       BOOLEAN     NOT NULL DEFAULT FALSE,
    nacionalidad        VARCHAR(60),

    -- ── Datos Laborales (cap. 4.4.2) ─────────────────────────────────────────
    tipo_sueldo         VARCHAR(1)  NOT NULL DEFAULT 'M'
        CHECK (tipo_sueldo IN ('M','D','H','E')),
        -- M=Mensual,D=Diario,H=Hora,E=Empresarial
    moneda_id           INT         NOT NULL DEFAULT 1 REFERENCES nomina.tipo_moneda(id),
    monto_sueldo        NUMERIC(12,2) NOT NULL DEFAULT 0,
    horas_semana        NUMERIC(5,2),
    dias_semana         SMALLINT    CHECK (dias_semana BETWEEN 1 AND 7),
    -- Gratificación
    tipo_gratificacion  VARCHAR(20) NOT NULL DEFAULT 'calculada'
        CHECK (tipo_gratificacion IN ('calculada','informada','proporcional','calculada_dict4232','no_paga')),
    monto_gratificacion NUMERIC(12,2),
    -- Otros antecedentes
    monto_movilizacion  NUMERIC(10,2) NOT NULL DEFAULT 0,
    monto_colacion      NUMERIC(10,2) NOT NULL DEFAULT 0,
    -- Forma de pago
    forma_pago          VARCHAR(1)  NOT NULL DEFAULT 'E'
        CHECK (forma_pago IN ('E','C','D','P')),
        -- E=Efectivo,C=Cheque,D=Depósito,P=PER
    banco_id            INT         REFERENCES nomina.banco(id),
    nro_cuenta          VARCHAR(30),
    tipo_mov_bancario   SMALLINT    REFERENCES nomina.tipo_movimiento_bancario(id),
    -- Características tributarias
    impuesto_agricola   BOOLEAN     NOT NULL DEFAULT FALSE,
    art61_ley18768      BOOLEAN     NOT NULL DEFAULT FALSE,
    pct_asignacion_zona NUMERIC(5,2) NOT NULL DEFAULT 0,
    incrementa_pct_zona BOOLEAN     NOT NULL DEFAULT FALSE,
    no_calcula_ajuste_sueldo BOOLEAN NOT NULL DEFAULT FALSE,
    -- Contratación
    fecha_contrato      DATE,
    profesion           VARCHAR(100),
    labor               VARCHAR(200),
    cargo_id            UUID        REFERENCES nomina.cargo(id),
    sucursal_id         UUID        REFERENCES nomina.sucursal(id),
    centro_costo_id     UUID        REFERENCES nomina.centro_costo(id),
    supervisor_id       UUID        REFERENCES rrhh.supervisor(id),
    tipo_contrato_id    UUID        REFERENCES nomina.tipo_contrato(id),

    -- ── Datos Previsionales (cap. 4.4.3) ─────────────────────────────────────
    regimen_previsional SMALLINT    NOT NULL DEFAULT 1
        CHECK (regimen_previsional IN (1,2,3,4)),
        -- 1=AFP,2=Régimen Antiguo(EMPART/SSS),3=No Cotiza,4=Téc.Extranjero Ley18.156
    afp_id              INT         REFERENCES nomina.afp(id),
    cotizacion_voluntaria_afp NUMERIC(12,2) NOT NULL DEFAULT 0,
    rebaja_imp_cotiz_vol BOOLEAN    NOT NULL DEFAULT FALSE,

    -- APV (Ahorro Previsional Voluntario) — relación 1:N en tabla aparte

    -- Régimen de salud
    regimen_salud       VARCHAR(10) NOT NULL DEFAULT 'FONASA'
        CHECK (regimen_salud IN ('FONASA','ISAPRE')),
    isapre_id           INT         REFERENCES nomina.isapre(id),
    modalidad_isapre    SMALLINT    CHECK (modalidad_isapre IN (1,2,3,4,5,6)),
        -- 1=Pesos,2=UF,3=7%,4=7%+UF,5=7%+UF+Pesos,6=Pesos+UF
    monto_isapre_pesos  NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto_isapre_uf     NUMERIC(8,4)  NOT NULL DEFAULT 0,

    -- Seguro de Cesantía
    tiene_seg_cesantia  BOOLEAN     NOT NULL DEFAULT TRUE,
    contrato_plazo_fijo BOOLEAN     NOT NULL DEFAULT FALSE,
    fecha_ingreso_sc    DATE,
    fecha_ultimo_mes_sc DATE,
    afp_seg_cesantia_id INT         REFERENCES nomina.afp(id),
    no_cotiza_sis       BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Ley 19.966 GES/AUGE
    beneficiarios_ges   SMALLINT    NOT NULL DEFAULT 0,
    vigencia_ges        SMALLINT    CHECK (vigencia_ges IN (0,1)),

    -- Servicio Médico CCHC
    tiene_serv_med_cchc BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Tipo de trabajador (para Previred)
    tipo_trabajador     SMALLINT    NOT NULL DEFAULT 1
        CHECK (tipo_trabajador IN (1,2,3,4)),
        -- 1=Activo NoPensionado,2=Pensionado Cotiza,3=Pensionado NoCotiza,4=Activo>60o65

    es_activo           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_id, rut),
    UNIQUE (tenant_id, codigo)
);

ALTER TABLE rrhh.trabajador ENABLE ROW LEVEL SECURITY;
CREATE POLICY trabajador_tenant_isolation ON rrhh.trabajador
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_trabajador_tenant     ON rrhh.trabajador(tenant_id);
CREATE INDEX ix_trabajador_rut        ON rrhh.trabajador(tenant_id, rut);
CREATE INDEX ix_trabajador_activo     ON rrhh.trabajador(tenant_id, es_activo);
CREATE INDEX ix_trabajador_cargo      ON rrhh.trabajador(cargo_id);
CREATE INDEX ix_trabajador_sucursal   ON rrhh.trabajador(sucursal_id);
CREATE INDEX ix_trabajador_cc         ON rrhh.trabajador(centro_costo_id);


-- ─── APV (Ahorro Previsional Voluntario) ──────────────────────────────────────
-- Fuente: Manual cap. 4.4.3 (APV individual y colectivo)
CREATE TABLE rrhh.trabajador_apv (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id       UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    tipo_apv            VARCHAR(10) NOT NULL CHECK (tipo_apv IN ('normal','colectivo')),
    moneda_trabajador   VARCHAR(5)  NOT NULL DEFAULT 'CLP'
        CHECK (moneda_trabajador IN ('CLP','UF','PCT')),
    monto_trabajador    NUMERIC(12,4) NOT NULL DEFAULT 0,
    -- Solo APV colectivo
    moneda_empleador    VARCHAR(5)  CHECK (moneda_empleador IN ('CLP','UF','PCT')),
    monto_empleador     NUMERIC(12,4) NOT NULL DEFAULT 0,
    -- Administrador
    administra_afp      BOOLEAN     NOT NULL DEFAULT TRUE,
    afp_id              INT         REFERENCES nomina.afp(id),
    otra_institucion    VARCHAR(100),
    rebaja_art42bis     BOOLEAN     NOT NULL DEFAULT FALSE,
    fecha_inicio        DATE        NOT NULL,
    fecha_termino       DATE,
    es_activo           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.trabajador_apv ENABLE ROW LEVEL SECURITY;
CREATE POLICY trabajador_apv_tenant_isolation ON rrhh.trabajador_apv
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_apv_trabajador ON rrhh.trabajador_apv(trabajador_id);


-- ─── DATOS CÓNYUGE AFILIADO VOLUNTARIO ────────────────────────────────────────
-- Fuente: Manual cap. 4.4.3 (Datos Cónyuge, Ley 20.255)
CREATE TABLE rrhh.trabajador_conyuge_afiliado (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    rut_conyuge     VARCHAR(12) NOT NULL,
    nombres         VARCHAR(200) NOT NULL,
    afp_id          INT         REFERENCES nomina.afp(id),
    monto_cotiz_voluntaria NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto_deposito_ahorro  NUMERIC(12,2) NOT NULL DEFAULT 0,
    fecha_inicio    DATE        NOT NULL,
    fecha_termino   DATE,
    cesar_cotizacion BOOLEAN    NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, trabajador_id)
);

ALTER TABLE rrhh.trabajador_conyuge_afiliado ENABLE ROW LEVEL SECURITY;
CREATE POLICY conyuge_afil_tenant_isolation ON rrhh.trabajador_conyuge_afiliado
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── CARGAS FAMILIARES ────────────────────────────────────────────────────────
-- Fuente: Manual cap. 4.4.4
CREATE TABLE rrhh.carga_familiar (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    rut             VARCHAR(12) NOT NULL,
    nombres         VARCHAR(200) NOT NULL,
    fecha_nacimiento DATE       NOT NULL,
    fecha_vencimiento DATE      NOT NULL,
    tipo_carga      VARCHAR(10) NOT NULL CHECK (tipo_carga IN ('simple','maternal','invalidez')),
    parentesco      VARCHAR(15) NOT NULL CHECK (parentesco IN ('hijo','conyuge','progenitor','hermano')),
    es_activa       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.carga_familiar ENABLE ROW LEVEL SECURITY;
CREATE POLICY carga_familiar_tenant_isolation ON rrhh.carga_familiar
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_carga_familiar_trabajador ON rrhh.carga_familiar(trabajador_id);
CREATE INDEX ix_carga_familiar_tenant     ON rrhh.carga_familiar(tenant_id);


-- ─── VALOR ASIGNACIÓN FAMILIAR POR MES ────────────────────────────────────────
-- Fuente: Manual cap. 4.4.4 (sección inferior: sueldo imponible por mes para cálculo proporcional)
CREATE TABLE rrhh.carga_familiar_sueldo_mensual (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    anio            SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    sueldo_imponible NUMERIC(12,2) NOT NULL DEFAULT 0,
    UNIQUE (tenant_id, trabajador_id, anio, mes)
);

ALTER TABLE rrhh.carga_familiar_sueldo_mensual ENABLE ROW LEVEL SECURITY;
CREATE POLICY cf_sueldo_mensual_tenant_isolation ON rrhh.carga_familiar_sueldo_mensual
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── FICHA VACACIONES ────────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.3.1, 8.9.1
CREATE TABLE rrhh.ficha_vacacion (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evento    DATE        NOT NULL,
    descripcion     VARCHAR(200),          -- tipo de evento
    fecha_desde     DATE        NOT NULL,
    fecha_hasta     DATE        NOT NULL,
    dias_otorgados  NUMERIC(5,2) NOT NULL DEFAULT 0,
    dias_utilizados NUMERIC(5,2) NOT NULL DEFAULT 0,
    es_progresiva   BOOLEAN     NOT NULL DEFAULT FALSE,
    comprobante_path TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.ficha_vacacion ENABLE ROW LEVEL SECURITY;
CREATE POLICY ficha_vacacion_tenant_isolation ON rrhh.ficha_vacacion
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_ficha_vacacion_trabajador ON rrhh.ficha_vacacion(trabajador_id);
CREATE INDEX ix_ficha_vacacion_tenant     ON rrhh.ficha_vacacion(tenant_id);


-- ─── FICHA PERMISOS ───────────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.3.2
CREATE TABLE rrhh.ficha_permiso (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evento    DATE        NOT NULL,
    tipo_permiso_id UUID        NOT NULL REFERENCES rrhh.tipo_permiso(id),
    fecha_desde     DATE        NOT NULL,
    fecha_hasta     DATE        NOT NULL,
    dias_otorgados  NUMERIC(5,2) NOT NULL DEFAULT 0,
    observaciones   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.ficha_permiso ENABLE ROW LEVEL SECURITY;
CREATE POLICY ficha_permiso_tenant_isolation ON rrhh.ficha_permiso
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE INDEX ix_ficha_permiso_trabajador ON rrhh.ficha_permiso(trabajador_id);


-- ─── FICHA PRÉSTAMOS RRHH ────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.3.3
-- NOTA: los préstamos operativos de descuento están en nomina.prestamo.
--       Esta ficha es el registro histórico en la vista RRHH.
CREATE TABLE rrhh.ficha_prestamo (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evento    DATE        NOT NULL,
    tipo            VARCHAR(10) NOT NULL CHECK (tipo IN ('otorgado','abono')),
    monto           NUMERIC(12,2) NOT NULL DEFAULT 0,
    comentario      TEXT,
    prestamo_id     UUID,       -- referencia opcional a nomina.prestamo
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.ficha_prestamo ENABLE ROW LEVEL SECURITY;
CREATE POLICY ficha_prestamo_tenant_isolation ON rrhh.ficha_prestamo
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── CARGOS DESEMPEÑADOS ─────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.3.4
CREATE TABLE rrhh.cargo_desempenado (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    cargo_id        UUID        REFERENCES nomina.cargo(id),
    cargo_descripcion VARCHAR(100),  -- permite texto libre si no existe en catálogo
    fecha_desde     DATE        NOT NULL,
    fecha_hasta     DATE,
    observaciones   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.cargo_desempenado ENABLE ROW LEVEL SECURITY;
CREATE POLICY cargo_desemp_tenant_isolation ON rrhh.cargo_desempenado
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── OBSERVACIONES RRHH ──────────────────────────────────────────────────────
-- Fuente: Manual cap. 8.3.5
CREATE TABLE rrhh.observacion (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evento    DATE        NOT NULL,
    supervisor_id   UUID        REFERENCES rrhh.supervisor(id),
    tipo            VARCHAR(50),
    descripcion     TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.observacion ENABLE ROW LEVEL SECURITY;
CREATE POLICY observacion_tenant_isolation ON rrhh.observacion
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── EVALUACIONES CUANTITATIVAS DEL TRABAJADOR ────────────────────────────────
-- Fuente: Manual cap. 8.3.7, 8.4
CREATE TABLE rrhh.trabajador_eval_cuantitativa (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evaluacion DATE       NOT NULL,
    evaluacion_id   UUID        NOT NULL REFERENCES rrhh.evaluacion_cuantitativa(id),
    atributo_id     UUID        NOT NULL REFERENCES rrhh.atributo_eval_cuantitativa(id),
    valor           NUMERIC(6,2) NOT NULL,
    observaciones   TEXT,
    creado_por_id   UUID        REFERENCES public.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.trabajador_eval_cuantitativa ENABLE ROW LEVEL SECURITY;
CREATE POLICY trab_eval_cuan_tenant_isolation ON rrhh.trabajador_eval_cuantitativa
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── EVALUACIONES CUALITATIVAS DEL TRABAJADOR ────────────────────────────────
-- Fuente: Manual cap. 8.3.8, 8.7
CREATE TABLE rrhh.trabajador_eval_cualitativa (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evaluacion DATE       NOT NULL,
    evaluacion_id   UUID        NOT NULL REFERENCES rrhh.evaluacion_cualitativa(id),
    atributo_id     UUID        NOT NULL REFERENCES rrhh.atributo_eval_cualitativa(id),
    descripcion     TEXT,
    creado_por_id   UUID        REFERENCES public.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.trabajador_eval_cualitativa ENABLE ROW LEVEL SECURITY;
CREATE POLICY trab_eval_cual_tenant_isolation ON rrhh.trabajador_eval_cualitativa
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ─── CONTRATOS RRHH (referencia histórica) ────────────────────────────────────
-- Fuente: Manual cap. 8.3.9
-- Referencia/vista desde RRHH hacia contratos de Nómina
CREATE TABLE rrhh.contrato_rrhh (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trabajador_id   UUID        NOT NULL REFERENCES rrhh.trabajador(id) ON DELETE CASCADE,
    fecha_evento    DATE        NOT NULL,
    supervisor_id   UUID        REFERENCES rrhh.supervisor(id),
    contrato_id     UUID,       -- referencia a nomina.contrato
    descripcion     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rrhh.contrato_rrhh ENABLE ROW LEVEL SECURITY;
CREATE POLICY contrato_rrhh_tenant_isolation ON rrhh.contrato_rrhh
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);
