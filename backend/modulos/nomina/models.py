"""
modulos/nomina/models.py
========================
Modelos SQLAlchemy para el módulo de Nómina (Remuneraciones).

Convenciones:
- Tablas globales (catálogos): sin tenant_id, __table_args__ sin RLS comment.
- Tablas operacionales: con tenant_id + Index + RLS habilitado en schema.sql.
- Todas las FK a tablas del core usan string "tenants.id" / "users.id" (public schema).
- FK entre módulos usan string "nomina.<tabla>.id" o "rrhh.<tabla>.id".
- __tablename__ incluye schema prefix vía MetaData o __table_args__.schema.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, SmallInteger, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship

from app.db.session import Base  # Base del proyecto raíz


def utcnow():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS GLOBALES (sin tenant_id)
# ─────────────────────────────────────────────────────────────────────────────

class Afp(Base):
    """AFP vigentes en Chile. Seed al iniciar sistema."""
    __tablename__ = "afp"
    __table_args__ = {"schema": "nomina"}

    id                = Column(Integer, primary_key=True, autoincrement=True)
    codigo_previred   = Column(SmallInteger, nullable=False, unique=True)
    nombre            = Column(String(100), nullable=False)
    nombre_corto      = Column(String(30), nullable=False)
    tasa_trabajador   = Column(Numeric(5, 4), nullable=False)
    tasa_sis          = Column(Numeric(5, 4), nullable=False, default=0)
    tasa_trabajo_pesado = Column(Numeric(5, 4), nullable=False, default=0)
    es_activa         = Column(Boolean, nullable=False, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Isapre(Base):
    """Isapres y Fonasa vigentes en Chile."""
    __tablename__ = "isapre"
    __table_args__ = {"schema": "nomina"}

    id                = Column(Integer, primary_key=True, autoincrement=True)
    codigo_previred   = Column(SmallInteger, nullable=False, unique=True)
    nombre            = Column(String(100), nullable=False)
    nombre_corto      = Column(String(30), nullable=False)
    es_activa         = Column(Boolean, nullable=False, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Ccaf(Base):
    """Cajas de Compensación y Asignación Familiar."""
    __tablename__ = "ccaf"
    __table_args__ = {"schema": "nomina"}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    codigo      = Column(String(10), nullable=False, unique=True)
    nombre      = Column(String(100), nullable=False)
    nombre_corto = Column(String(30), nullable=False)
    es_activa   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Mutualidad(Base):
    """Mutualidades de Seguridad (accidentes del trabajo)."""
    __tablename__ = "mutualidad"
    __table_args__ = {"schema": "nomina"}

    id              = Column(Integer, primary_key=True, autoincrement=True)
    codigo          = Column(String(10), nullable=False, unique=True)
    nombre          = Column(String(100), nullable=False)
    nombre_corto    = Column(String(30), nullable=False)
    tasa_cotizacion = Column(Numeric(5, 4), nullable=False, default=0)
    es_activa       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Banco(Base):
    """Tabla de bancos (Tabla N°2 manual Transtecnia)."""
    __tablename__ = "banco"
    __table_args__ = {"schema": "nomina"}

    id        = Column(Integer, primary_key=True, autoincrement=True)
    codigo    = Column(SmallInteger, nullable=False, unique=True)
    nombre    = Column(String(100), nullable=False)
    es_activo = Column(Boolean, nullable=False, default=True)


class TipoMovimientoBancario(Base):
    """Tipos de movimiento bancario para pago remuneraciones (Tabla N°3)."""
    __tablename__ = "tipo_movimiento_bancario"
    __table_args__ = {"schema": "nomina"}

    id          = Column(SmallInteger, primary_key=True)
    descripcion = Column(String(60), nullable=False)


class Region(Base):
    """Regiones de Chile."""
    __tablename__ = "region"
    __table_args__ = {"schema": "nomina"}

    id             = Column(SmallInteger, primary_key=True)
    codigo         = Column(String(5), nullable=False, unique=True)
    nombre         = Column(String(100), nullable=False)
    es_zona_extrema = Column(Boolean, nullable=False, default=False)

    comunas = relationship("Comuna", back_populates="region")


class Comuna(Base):
    """Comunas de Chile (Tabla N°1 manual Transtecnia)."""
    __tablename__ = "comuna"
    __table_args__ = {"schema": "nomina"}

    codigo    = Column(SmallInteger, primary_key=True)
    nombre    = Column(String(80), nullable=False)
    region_id = Column(SmallInteger, ForeignKey("nomina.region.id"), nullable=False)

    region = relationship("Region", back_populates="comunas")


class TipoMoneda(Base):
    """Tipos de moneda soportados (CLP, UF, UTM, etc.)."""
    __tablename__ = "tipo_moneda"
    __table_args__ = {"schema": "nomina"}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    codigo      = Column(String(10), nullable=False, unique=True)
    descripcion = Column(String(60), nullable=False)
    es_activa   = Column(Boolean, nullable=False, default=True)


class TramoAsignacionFamiliar(Base):
    """Tramos de asignación familiar por año/mes (cap. 5.1.2)."""
    __tablename__ = "tramo_asignacion_familiar"
    __table_args__ = (
        UniqueConstraint("anio", "mes", "tramo"),
        {"schema": "nomina"},
    )

    id          = Column(Integer, primary_key=True, autoincrement=True)
    anio        = Column(SmallInteger, nullable=False)
    mes         = Column(SmallInteger, nullable=False)
    tramo       = Column(SmallInteger, nullable=False)
    renta_desde = Column(Numeric(12, 2), nullable=False)
    renta_hasta = Column(Numeric(12, 2), nullable=True)
    valor_carga = Column(Numeric(10, 2), nullable=False)
    descripcion = Column(String(50), nullable=False)


class TramoImpuestoUnicoUTM(Base):
    """Tramos impuesto único 2ª categoría en UTM (cap. 5.1.3)."""
    __tablename__ = "tramo_impuesto_unico_utm"
    __table_args__ = (
        UniqueConstraint("anio", "mes", "orden"),
        {"schema": "nomina"},
    )

    id         = Column(Integer, primary_key=True, autoincrement=True)
    anio       = Column(SmallInteger, nullable=False)
    mes        = Column(SmallInteger, nullable=False)
    orden      = Column(SmallInteger, nullable=False)
    utm_desde  = Column(Numeric(8, 4), nullable=False)
    utm_hasta  = Column(Numeric(8, 4), nullable=True)
    tasa       = Column(Numeric(6, 4), nullable=False)
    rebaja_utm = Column(Numeric(8, 4), nullable=False, default=0)


class FactorActualizacion(Base):
    """UTM, UF, IMM e IPC por período (cap. 4.3)."""
    __tablename__ = "factor_actualizacion"
    __table_args__ = (
        UniqueConstraint("anio", "mes"),
        {"schema": "nomina"},
    )

    id      = Column(Integer, primary_key=True, autoincrement=True)
    anio    = Column(SmallInteger, nullable=False)
    mes     = Column(SmallInteger, nullable=False)
    utm     = Column(Numeric(12, 2), nullable=False)
    uf      = Column(Numeric(12, 4), nullable=False)
    factor  = Column(Numeric(10, 6), nullable=False, default=1.0)
    imm     = Column(Numeric(12, 2), nullable=False)


class ServMedCchc(Base):
    """Parámetros Servicio Médico Cámara Chilena de la Construcción (cap. 5.1.5)."""
    __tablename__ = "serv_med_cchc"
    __table_args__ = (
        UniqueConstraint("anio", "mes"),
        {"schema": "nomina"},
    )

    id          = Column(Integer, primary_key=True, autoincrement=True)
    anio        = Column(SmallInteger, nullable=False)
    mes         = Column(SmallInteger, nullable=False)
    porcentaje  = Column(Numeric(6, 4), nullable=False)
    tope_uf     = Column(Numeric(8, 4), nullable=False)
    valor_carga = Column(Numeric(10, 2), nullable=False, default=0)


# ─────────────────────────────────────────────────────────────────────────────
# TABLAS OPERACIONALES (con tenant_id + RLS)
# ─────────────────────────────────────────────────────────────────────────────

class EmpresaConfig(Base):
    """Extensión de tenant con datos tributarios/previsionales de la empresa (cap. 4.1)."""
    __tablename__ = "empresa_config"
    __table_args__ = (
        UniqueConstraint("tenant_id"),
        Index("ix_empresa_config_tenant", "tenant_id"),
        {"schema": "nomina"},
    )

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id             = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    nombre_rep_legal      = Column(String(200))
    rut_rep_legal         = Column(String(12))
    nombre_contador       = Column(String(200))
    rut_contador          = Column(String(12))
    giro                  = Column(String(200))
    ccaf_id               = Column(Integer, ForeignKey("nomina.ccaf.id"))
    mutualidad_id         = Column(Integer, ForeignKey("nomina.mutualidad.id"))
    modalidad_gratificacion = Column(String(20), nullable=False, default="calculada")
    logo_url              = Column(Text)
    numero_convenio_fun   = Column(String(50))
    mapi_nombre_remitente = Column(String(100))
    mapi_email_remitente  = Column(String(254))
    created_at            = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at            = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    ccaf       = relationship("Ccaf")
    mutualidad = relationship("Mutualidad")


class Sucursal(Base):
    """Sucursales de la empresa (cap. 4.12)."""
    __tablename__ = "sucursal"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        Index("ix_sucursal_tenant", "tenant_id"),
        {"schema": "nomina"},
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo          = Column(String(20), nullable=False)
    nombre          = Column(String(100), nullable=False)
    direccion       = Column(String(200))
    region_id       = Column(SmallInteger, ForeignKey("nomina.region.id"))
    comuna_id       = Column(SmallInteger, ForeignKey("nomina.comuna.codigo"))
    codigo_pais     = Column(String(5), default="CL")
    telefono        = Column(String(30))
    codigo_previred = Column(String(20))
    es_activa       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    region = relationship("Region")
    comuna = relationship("Comuna")


class CentroCosto(Base):
    """Centros de costo (cap. 4.5)."""
    __tablename__ = "centro_costo"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        Index("ix_centro_costo_tenant", "tenant_id"),
        {"schema": "nomina"},
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo          = Column(String(20), nullable=False)
    descripcion     = Column(String(100), nullable=False)
    codigo_previred = Column(String(20))
    es_activo       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)


class Cargo(Base):
    """Cargos de la empresa (cap. 4.6)."""
    __tablename__ = "cargo"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "nomina"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(100), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TipoContrato(Base):
    """Tipos de contrato (cap. 4.8)."""
    __tablename__ = "tipo_contrato"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "nomina"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(100), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CausalFiniquito(Base):
    """Causales de término de contrato (cap. 4.9)."""
    __tablename__ = "causal_finiquito"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "nomina"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(200), nullable=False)
    articulo    = Column(String(50))
    es_activa   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ClausulaAdicional(Base):
    """Cláusulas adicionales para contratos (cap. 4.10)."""
    __tablename__ = "clausula_adicional"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "nomina"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(200), nullable=False)
    texto       = Column(Text, nullable=False)
    es_activa   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ConceptoRemuneracion(Base):
    """
    Haberes y descuentos configurables por tenant (cap. 4.7).
    Incluye todas las propiedades tributarias, previsionales y de cálculo.
    """
    __tablename__ = "concepto_remuneracion"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        Index("ix_concepto_rem_tenant", "tenant_id"),
        Index("ix_concepto_rem_tipo", "tenant_id", "tipo"),
        {"schema": "nomina"},
    )

    id                     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id              = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo                 = Column(String(10), nullable=False)
    descripcion            = Column(String(100), nullable=False)
    tipo                   = Column(String(1), nullable=False)     # 'H' | 'D'

    # Propiedades tributarias/previsionales
    es_imponible           = Column(Boolean, nullable=False, default=True)
    es_tributable          = Column(Boolean, nullable=False, default=True)
    es_renta_exenta        = Column(Boolean, nullable=False, default=False)
    reliquida_impuesto     = Column(Boolean, nullable=False, default=False)

    # Propiedades de cálculo
    es_fijo                = Column(Boolean, nullable=False, default=True)
    es_valor_diario        = Column(Boolean, nullable=False, default=False)
    es_semana_corrida      = Column(Boolean, nullable=False, default=False)
    es_porcentaje          = Column(Boolean, nullable=False, default=False)
    es_adicional_horas_ext = Column(Boolean, nullable=False, default=False)
    es_horas_extras        = Column(Boolean, nullable=False, default=False)
    adiciona_sueldo_imm    = Column(Boolean, nullable=False, default=False)
    es_haber_variable      = Column(Boolean, nullable=False, default=False)

    # Descuentos especiales
    es_anticipo            = Column(Boolean, nullable=False, default=False)
    es_prestamo_ccaf       = Column(Boolean, nullable=False, default=False)
    es_prestamo            = Column(Boolean, nullable=False, default=False)

    # LRE
    clasificacion_lre      = Column(String(50))
    exportable_lre         = Column(Boolean, nullable=False, default=False)

    es_activo              = Column(Boolean, nullable=False, default=True)
    created_at             = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at             = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)


class ParametroMensual(Base):
    """Parámetros de proceso por empresa/período (cap. 5.1)."""
    __tablename__ = "parametro_mensual"
    __table_args__ = (
        UniqueConstraint("tenant_id", "anio", "mes"),
        Index("ix_param_mensual_tenant_periodo", "tenant_id", "anio", "mes"),
        {"schema": "nomina"},
    )

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id            = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    anio                 = Column(SmallInteger, nullable=False)
    mes                  = Column(SmallInteger, nullable=False)
    utm                  = Column(Numeric(12, 2), nullable=False)
    uf                   = Column(Numeric(12, 4), nullable=False)
    imm                  = Column(Numeric(12, 2), nullable=False)
    factor_actualizacion = Column(Numeric(10, 6), nullable=False, default=1.0)
    tope_imponible_afp   = Column(Numeric(12, 2), nullable=False)
    tope_imponible_salud = Column(Numeric(12, 2), nullable=False)
    tope_seg_cesantia    = Column(Numeric(12, 2), nullable=False)
    tasa_acc_trabajo     = Column(Numeric(6, 4), nullable=False, default=0.0093)
    tasa_apv_colectivo   = Column(Numeric(6, 4), nullable=False, default=0)
    bloqueado            = Column(Boolean, nullable=False, default=False)
    cerrado              = Column(Boolean, nullable=False, default=False)
    fecha_cierre         = Column(DateTime(timezone=True))
    created_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at           = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)


class MovimientoMensual(Base):
    """
    Cabecera del proceso mensual por trabajador (cap. 5.2).
    Un trabajador puede tener múltiples movimientos en un mes (finiquito + recontratación).
    """
    __tablename__ = "movimiento_mensual"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trabajador_id", "anio", "mes", "nro_movimiento"),
        Index("ix_mov_mensual_tenant_periodo", "tenant_id", "anio", "mes"),
        Index("ix_mov_mensual_trabajador", "tenant_id", "trabajador_id"),
        Index("ix_movimiento_mensual_estado", "tenant_id", "estado"),
        {"schema": "nomina"},
    )

    id                           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id                    = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id                = Column(UUID(as_uuid=True), nullable=False)   # FK a rrhh.trabajador
    anio                         = Column(SmallInteger, nullable=False)
    mes                          = Column(SmallInteger, nullable=False)
    nro_movimiento               = Column(SmallInteger, nullable=False, default=1)

    dias_ausentes                = Column(Numeric(5, 2), nullable=False, default=0)
    dias_no_contratado           = Column(Numeric(5, 2), nullable=False, default=0)
    dias_licencia                = Column(Numeric(5, 2), nullable=False, default=0)
    dias_movilizacion            = Column(Numeric(5, 2), nullable=False, default=0)
    dias_colacion                = Column(Numeric(5, 2), nullable=False, default=0)
    dias_vacaciones              = Column(Numeric(5, 2), nullable=False, default=0)

    otras_rentas                 = Column(Numeric(12, 2), nullable=False, default=0)
    monto_isapre_otro            = Column(Numeric(12, 2), nullable=False, default=0)
    monto_salud_iu               = Column(Numeric(12, 2), nullable=False, default=0)

    hh_extras_normales           = Column(Numeric(6, 2), nullable=False, default=0)
    hh_extras_nocturnas          = Column(Numeric(6, 2), nullable=False, default=0)
    hh_extras_festivas           = Column(Numeric(6, 2), nullable=False, default=0)

    cargas_retroactivas          = Column(SmallInteger, nullable=False, default=0)
    cargas_retro_simples         = Column(SmallInteger, nullable=False, default=0)
    cargas_retro_invalidez       = Column(SmallInteger, nullable=False, default=0)
    cargas_retro_maternales      = Column(SmallInteger, nullable=False, default=0)

    codigo_movimiento            = Column(SmallInteger, nullable=False, default=0)
    fecha_inicio_mov             = Column(Date)
    fecha_termino_mov            = Column(Date)
    fecha_inicio_licencia        = Column(Date)
    fecha_termino_licencia       = Column(Date)
    rut_entidad_pagadora         = Column(String(12))
    imponible_sc_mes_anterior    = Column(Numeric(12, 2), nullable=False, default=0)
    imponible_prev_mes_anterior  = Column(Numeric(12, 2), nullable=False, default=0)

    # Resultados del cálculo
    total_haberes                = Column(Numeric(12, 2))
    total_imponible              = Column(Numeric(12, 2))
    total_tributable             = Column(Numeric(12, 2))
    descuento_afp                = Column(Numeric(12, 2))
    descuento_salud              = Column(Numeric(12, 2))
    impuesto_unico               = Column(Numeric(12, 2))
    total_descuentos             = Column(Numeric(12, 2))
    liquido_pagar                = Column(Numeric(12, 2))
    anticipo                     = Column(Numeric(12, 2), nullable=False, default=0)

    estado                       = Column(String(20), nullable=False, default="pendiente")
    calculado_en                 = Column(DateTime(timezone=True))
    created_at                   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at                   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    # Relaciones
    conceptos = relationship("MovimientoConcepto", back_populates="movimiento", cascade="all, delete-orphan")


class MovimientoConcepto(Base):
    """Haberes y descuentos asignados al movimiento mensual (cap. 5.2.2)."""
    __tablename__ = "movimiento_concepto"
    __table_args__ = (
        Index("ix_mov_concepto_movimiento", "movimiento_id"),
        Index("ix_mov_concepto_tenant", "tenant_id"),
        {"schema": "nomina"},
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    movimiento_id    = Column(UUID(as_uuid=True), ForeignKey("nomina.movimiento_mensual.id", ondelete="CASCADE"), nullable=False)
    concepto_id      = Column(UUID(as_uuid=True), ForeignKey("nomina.concepto_remuneracion.id"), nullable=False)
    tipo             = Column(String(1), nullable=False)  # 'H' | 'D'
    valor            = Column(Numeric(12, 2), nullable=False, default=0)
    cantidad         = Column(Numeric(9, 4), nullable=False, default=1)
    ocurrencia       = Column(SmallInteger, nullable=False, default=1)
    monto_calculado  = Column(Numeric(12, 2), nullable=False, default=0)
    es_semana_corrida = Column(Boolean, nullable=False, default=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    movimiento = relationship("MovimientoMensual", back_populates="conceptos")
    concepto   = relationship("ConceptoRemuneracion")


class Contrato(Base):
    """Contrato de trabajo (cap. 5.4)."""
    __tablename__ = "contrato"
    __table_args__ = (
        Index("ix_contrato_tenant", "tenant_id"),
        Index("ix_contrato_trabajador", "tenant_id", "trabajador_id"),
        {"schema": "nomina"},
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id    = Column(UUID(as_uuid=True), nullable=False)
    nro_contrato     = Column(String(20))
    tipo_contrato_id = Column(UUID(as_uuid=True), ForeignKey("nomina.tipo_contrato.id"))
    fecha_inicio     = Column(Date, nullable=False)
    fecha_termino    = Column(Date)
    cargo_id         = Column(UUID(as_uuid=True), ForeignKey("nomina.cargo.id"))
    sucursal_id      = Column(UUID(as_uuid=True), ForeignKey("nomina.sucursal.id"))
    centro_costo_id  = Column(UUID(as_uuid=True), ForeignKey("nomina.centro_costo.id"))
    labor            = Column(String(200))
    establecimiento  = Column(String(200))
    horario_beneficios = Column(String(100))
    fecha_emision    = Column(Date)
    observaciones    = Column(Text)
    estado           = Column(String(20), nullable=False, default="vigente")
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    tipo_contrato  = relationship("TipoContrato")
    cargo          = relationship("Cargo")
    sucursal       = relationship("Sucursal")
    centro_costo   = relationship("CentroCosto")
    clausulas      = relationship("ContratoClausula", back_populates="contrato", cascade="all, delete-orphan")


class ContratoClausula(Base):
    """Cláusulas adicionales asociadas a un contrato."""
    __tablename__ = "contrato_clausula"
    __table_args__ = {"schema": "nomina"}

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id           = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    contrato_id         = Column(UUID(as_uuid=True), ForeignKey("nomina.contrato.id", ondelete="CASCADE"), nullable=False)
    clausula_id         = Column(UUID(as_uuid=True), ForeignKey("nomina.clausula_adicional.id"), nullable=False)
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    contrato  = relationship("Contrato", back_populates="clausulas")
    clausula  = relationship("ClausulaAdicional")


class Finiquito(Base):
    """Finiquito de trabajador (cap. 5.5)."""
    __tablename__ = "finiquito"
    __table_args__ = (
        Index("ix_finiquito_tenant", "tenant_id"),
        Index("ix_finiquito_trabajador", "tenant_id", "trabajador_id"),
        {"schema": "nomina"},
    )

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id           = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id       = Column(UUID(as_uuid=True), nullable=False)
    movimiento_id       = Column(UUID(as_uuid=True), ForeignKey("nomina.movimiento_mensual.id"))
    contrato_id         = Column(UUID(as_uuid=True), ForeignKey("nomina.contrato.id"))
    fecha_inicio        = Column(Date, nullable=False)
    fecha_finiquito     = Column(Date, nullable=False)
    cargo_id            = Column(UUID(as_uuid=True), ForeignKey("nomina.cargo.id"))
    causal_id           = Column(UUID(as_uuid=True), ForeignKey("nomina.causal_finiquito.id"))
    descripcion_pago    = Column(Text)
    importa_liquidacion = Column(Boolean, nullable=False, default=False)
    total_finiquito     = Column(Numeric(12, 2))
    estado              = Column(String(20), nullable=False, default="borrador")
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    causal    = relationship("CausalFiniquito")
    cargo     = relationship("Cargo")
    conceptos = relationship("FiniquitoConcepto", back_populates="finiquito", cascade="all, delete-orphan")


class FiniquitoConcepto(Base):
    """Conceptos del finiquito (cap. 5.5.2)."""
    __tablename__ = "finiquito_concepto"
    __table_args__ = {"schema": "nomina"}

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id    = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    finiquito_id = Column(UUID(as_uuid=True), ForeignKey("nomina.finiquito.id", ondelete="CASCADE"), nullable=False)
    descripcion  = Column(String(200), nullable=False)
    monto        = Column(Numeric(12, 2), nullable=False, default=0)
    es_haber     = Column(Boolean, nullable=False, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    finiquito = relationship("Finiquito", back_populates="conceptos")


class Prestamo(Base):
    """Préstamo otorgado a trabajador (cap. 8.10)."""
    __tablename__ = "prestamo"
    __table_args__ = (
        Index("ix_prestamo_tenant", "tenant_id"),
        Index("ix_prestamo_trabajador", "tenant_id", "trabajador_id"),
        Index("ix_prestamo_estado", "tenant_id", "estado"),
        {"schema": "nomina"},
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id   = Column(UUID(as_uuid=True), nullable=False)
    concepto_id     = Column(UUID(as_uuid=True), ForeignKey("nomina.concepto_remuneracion.id"), nullable=False)
    monto_total     = Column(Numeric(12, 2), nullable=False)
    nro_cuotas      = Column(SmallInteger, nullable=False)
    valor_cuota     = Column(Numeric(12, 2), nullable=False)
    fecha_inicio    = Column(Date, nullable=False)
    saldo_pendiente = Column(Numeric(12, 2), nullable=False)
    estado          = Column(String(20), nullable=False, default="activo")
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    concepto = relationship("ConceptoRemuneracion")
    cuotas   = relationship("PrestamoCuota", back_populates="prestamo", cascade="all, delete-orphan")


class PrestamoCuota(Base):
    """Cuotas individuales de un préstamo (cap. 8.10.1)."""
    __tablename__ = "prestamo_cuota"
    __table_args__ = (
        UniqueConstraint("prestamo_id", "nro_cuota"),
        {"schema": "nomina"},
    )

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    prestamo_id   = Column(UUID(as_uuid=True), ForeignKey("nomina.prestamo.id", ondelete="CASCADE"), nullable=False)
    nro_cuota     = Column(SmallInteger, nullable=False)
    anio          = Column(SmallInteger, nullable=False)
    mes           = Column(SmallInteger, nullable=False)
    monto         = Column(Numeric(12, 2), nullable=False)
    procesar      = Column(Boolean, nullable=False, default=True)
    pagada        = Column(Boolean, nullable=False, default=False)
    fecha_pago    = Column(Date)
    movimiento_id = Column(UUID(as_uuid=True), ForeignKey("nomina.movimiento_mensual.id"))

    prestamo = relationship("Prestamo", back_populates="cuotas")


class Anticipo(Base):
    """Anticipos de remuneraciones (cap. 6.4, 7.6)."""
    __tablename__ = "anticipo"
    __table_args__ = (
        Index("ix_anticipo_tenant", "tenant_id"),
        Index("ix_anticipo_trabajador", "tenant_id", "trabajador_id"),
        {"schema": "nomina"},
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id   = Column(UUID(as_uuid=True), nullable=False)
    anio            = Column(SmallInteger, nullable=False)
    mes             = Column(SmallInteger, nullable=False)
    monto           = Column(Numeric(12, 2), nullable=False)
    fecha_emision   = Column(Date, nullable=False)
    sucursal_id     = Column(UUID(as_uuid=True), ForeignKey("nomina.sucursal.id"))
    centro_costo_id = Column(UUID(as_uuid=True), ForeignKey("nomina.centro_costo.id"))
    estado          = Column(String(20), nullable=False, default="pendiente")
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CertificadoImpuesto(Base):
    """Certificado anual de retenciones / DJ 1887 (cap. 6.5)."""
    __tablename__ = "certificado_impuesto"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trabajador_id", "anio_comercial"),
        {"schema": "nomina"},
    )

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id           = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id       = Column(UUID(as_uuid=True), nullable=False)
    anio_comercial      = Column(SmallInteger, nullable=False)
    nro_certificado     = Column(Integer, nullable=False)
    fecha_emision       = Column(Date, nullable=False)
    renta_bruta         = Column(Numeric(12, 2), nullable=False, default=0)
    renta_imponible     = Column(Numeric(12, 2), nullable=False, default=0)
    dcto_afp            = Column(Numeric(12, 2), nullable=False, default=0)
    dcto_salud          = Column(Numeric(12, 2), nullable=False, default=0)
    impuesto_unico      = Column(Numeric(12, 2), nullable=False, default=0)
    mayor_retencion     = Column(Numeric(12, 2), nullable=False, default=0)
    rentas_no_gravadas  = Column(Numeric(12, 2), nullable=False, default=0)
    rebaja_zona_extrema = Column(Numeric(12, 2), nullable=False, default=0)
    rentas_accesorias   = Column(Numeric(12, 2), nullable=False, default=0)
    tipo_jornada        = Column(String(1))
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RetencionAnual(Base):
    """Retenciones 3% (Ley 21.252) por trabajador/período (cap. 6.5.6, 7.23)."""
    __tablename__ = "retencion_anual"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trabajador_id", "anio", "mes"),
        {"schema": "nomina"},
    )

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), nullable=False)
    anio          = Column(SmallInteger, nullable=False)
    mes           = Column(SmallInteger, nullable=False)
    monto         = Column(Numeric(12, 2), nullable=False, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LreGeneracion(Base):
    """Registro de generaciones del Libro de Remuneraciones Electrónico (cap. 7.22)."""
    __tablename__ = "lre_generacion"
    __table_args__ = (
        UniqueConstraint("tenant_id", "anio", "mes"),
        {"schema": "nomina"},
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    anio             = Column(SmallInteger, nullable=False)
    mes              = Column(SmallInteger, nullable=False)
    archivo_path     = Column(Text)
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    generado_por_id  = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    estado           = Column(String(20), nullable=False, default="generado")
