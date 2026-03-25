"""
modulos/rrhh/models.py
======================
Modelos SQLAlchemy para el módulo de RRHH (Recursos Humanos).

Contiene datos personales, laborales y todo lo relacionado con el trabajador
independiente de su remuneración. Las referencias a tablas de nómina (cargo,
sucursal, centro_costo, etc.) se hacen con string FK al schema nomina.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, SmallInteger, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS GLOBALES RRHH
# ─────────────────────────────────────────────────────────────────────────────

class TipoPermisoGlobal(Base):
    """Catálogo global de tipos de permiso (referencia)."""
    __tablename__ = "tipo_permiso_global"
    __table_args__ = {"schema": "rrhh"}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    codigo      = Column(String(20), nullable=False, unique=True)
    descripcion = Column(String(100), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)


class TipoCargoRrhhGlobal(Base):
    """Catálogo global de tipos de cargo para evaluaciones RRHH."""
    __tablename__ = "tipo_cargo_rrhh_global"
    __table_args__ = {"schema": "rrhh"}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    codigo      = Column(String(20), nullable=False, unique=True)
    descripcion = Column(String(100), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)


# ─────────────────────────────────────────────────────────────────────────────
# TABLAS OPERACIONALES (con tenant_id + RLS)
# ─────────────────────────────────────────────────────────────────────────────

class Supervisor(Base):
    """Supervisores por empresa (cap. 8.1)."""
    __tablename__ = "supervisor"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        Index("ix_supervisor_tenant", "tenant_id"),
        {"schema": "rrhh"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    nombre      = Column(String(200), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TipoPermiso(Base):
    """Tipos de permiso por empresa (cap. 8.2)."""
    __tablename__ = "tipo_permiso"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "rrhh"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(100), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AtributoEvalCuantitativa(Base):
    """Atributos para evaluaciones cuantitativas (cap. 8.5)."""
    __tablename__ = "atributo_eval_cuantitativa"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "rrhh"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(30), nullable=False)
    descripcion = Column(String(200), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvaluacionCuantitativa(Base):
    """Escalas de evaluación cuantitativa por empresa (cap. 8.4)."""
    __tablename__ = "evaluacion_cuantitativa"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "rrhh"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(100), nullable=False)
    valor_min   = Column(Numeric(5, 2), nullable=False, default=0)
    valor_max   = Column(Numeric(5, 2), nullable=False, default=100)
    es_activa   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AtributoEvalCualitativa(Base):
    """Atributos para evaluaciones cualitativas (cap. 8.8)."""
    __tablename__ = "atributo_eval_cualitativa"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "rrhh"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(30), nullable=False)
    descripcion = Column(String(200), nullable=False)
    es_activo   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvaluacionCualitativa(Base):
    """Opciones de evaluación cualitativa por empresa (cap. 8.7)."""
    __tablename__ = "evaluacion_cualitativa"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        {"schema": "rrhh"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(String(100), nullable=False)
    es_activa   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# TRABAJADOR — tabla central
# ─────────────────────────────────────────────────────────────────────────────

class Trabajador(Base):
    """
    Ficha completa del trabajador (cap. 4.4).
    Integra: Datos Personales (4.4.1), Laborales (4.4.2) y Previsionales (4.4.3).
    Las cargas familiares y APV van en tablas relacionadas.
    """
    __tablename__ = "trabajador"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rut"),
        UniqueConstraint("tenant_id", "codigo"),
        Index("ix_trabajador_tenant", "tenant_id"),
        Index("ix_trabajador_rut", "tenant_id", "rut"),
        Index("ix_trabajador_activo", "tenant_id", "es_activo"),
        Index("ix_trabajador_cargo", "cargo_id"),
        Index("ix_trabajador_sucursal", "sucursal_id"),
        Index("ix_trabajador_cc", "centro_costo_id"),
        {"schema": "rrhh"},
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    codigo           = Column(String(20), nullable=False)

    # ── Datos Personales ──────────────────────────────────────────────────────
    rut              = Column(String(12), nullable=False)   # "12345678-9"
    nombres          = Column(String(100), nullable=False)
    apellido_paterno = Column(String(100), nullable=False)
    apellido_materno = Column(String(100))
    fecha_nacimiento = Column(Date)
    email            = Column(String(254))
    codigo_pais      = Column(String(5), default="CL")
    telefono         = Column(String(30))
    direccion_calle  = Column(String(200))
    direccion_numero = Column(String(20))
    region_id        = Column(SmallInteger, ForeignKey("nomina.region.id"))
    comuna_id        = Column(SmallInteger, ForeignKey("nomina.comuna.codigo"))
    estado_civil     = Column(SmallInteger)    # 1=Soltero,2=Casado,3=Viudo,4=Separado
    sexo             = Column(String(1))       # 'M' | 'F'
    es_extranjero    = Column(Boolean, nullable=False, default=False)
    nacionalidad     = Column(String(60))

    # ── Datos Laborales ───────────────────────────────────────────────────────
    tipo_sueldo      = Column(String(1), nullable=False, default="M")  # M/D/H/E
    moneda_id        = Column(Integer, ForeignKey("nomina.tipo_moneda.id"), nullable=False, default=1)
    monto_sueldo     = Column(Numeric(12, 2), nullable=False, default=0)
    horas_semana     = Column(Numeric(5, 2))
    dias_semana      = Column(SmallInteger)

    tipo_gratificacion  = Column(String(20), nullable=False, default="calculada")
    monto_gratificacion = Column(Numeric(12, 2))

    monto_movilizacion = Column(Numeric(10, 2), nullable=False, default=0)
    monto_colacion     = Column(Numeric(10, 2), nullable=False, default=0)

    forma_pago         = Column(String(1), nullable=False, default="E")  # E/C/D/P
    banco_id           = Column(Integer, ForeignKey("nomina.banco.id"))
    nro_cuenta         = Column(String(30))
    tipo_mov_bancario  = Column(SmallInteger, ForeignKey("nomina.tipo_movimiento_bancario.id"))

    impuesto_agricola        = Column(Boolean, nullable=False, default=False)
    art61_ley18768           = Column(Boolean, nullable=False, default=False)
    pct_asignacion_zona      = Column(Numeric(5, 2), nullable=False, default=0)
    incrementa_pct_zona      = Column(Boolean, nullable=False, default=False)
    no_calcula_ajuste_sueldo = Column(Boolean, nullable=False, default=False)

    fecha_contrato   = Column(Date)
    profesion        = Column(String(100))
    labor            = Column(String(200))
    cargo_id         = Column(UUID(as_uuid=True), ForeignKey("nomina.cargo.id"))
    sucursal_id      = Column(UUID(as_uuid=True), ForeignKey("nomina.sucursal.id"))
    centro_costo_id  = Column(UUID(as_uuid=True), ForeignKey("nomina.centro_costo.id"))
    supervisor_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.supervisor.id"))
    tipo_contrato_id = Column(UUID(as_uuid=True), ForeignKey("nomina.tipo_contrato.id"))

    # ── Datos Previsionales ───────────────────────────────────────────────────
    regimen_previsional       = Column(SmallInteger, nullable=False, default=1)
    afp_id                    = Column(Integer, ForeignKey("nomina.afp.id"))
    cotizacion_voluntaria_afp = Column(Numeric(12, 2), nullable=False, default=0)
    rebaja_imp_cotiz_vol      = Column(Boolean, nullable=False, default=False)

    regimen_salud       = Column(String(10), nullable=False, default="FONASA")
    isapre_id           = Column(Integer, ForeignKey("nomina.isapre.id"))
    modalidad_isapre    = Column(SmallInteger)
    monto_isapre_pesos  = Column(Numeric(12, 2), nullable=False, default=0)
    monto_isapre_uf     = Column(Numeric(8, 4), nullable=False, default=0)

    tiene_seg_cesantia  = Column(Boolean, nullable=False, default=True)
    contrato_plazo_fijo = Column(Boolean, nullable=False, default=False)
    fecha_ingreso_sc    = Column(Date)
    fecha_ultimo_mes_sc = Column(Date)
    afp_seg_cesantia_id = Column(Integer, ForeignKey("nomina.afp.id"))
    no_cotiza_sis       = Column(Boolean, nullable=False, default=False)

    beneficiarios_ges   = Column(SmallInteger, nullable=False, default=0)
    vigencia_ges        = Column(SmallInteger)

    tiene_serv_med_cchc = Column(Boolean, nullable=False, default=False)
    tipo_trabajador     = Column(SmallInteger, nullable=False, default=1)

    es_activo  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    # ── Relaciones intra-módulo ───────────────────────────────────────────────
    # NOTA: relationships a tablas nomina.* (Afp, Isapre, Banco, etc.) se omiten
    # intencionalmente para evitar conflictos de registry cross-módulo.
    # Las FK siguen funcionando; acceder a esos datos requiere un join explícito.
    supervisor       = relationship("Supervisor")

    cargas_familiares   = relationship("CargaFamiliar", back_populates="trabajador", cascade="all, delete-orphan")
    apvs                = relationship("TrabajadorApv", back_populates="trabajador", cascade="all, delete-orphan")
    conyuge_afiliado    = relationship("TrabajadorConyugeAfiliado", back_populates="trabajador", uselist=False, cascade="all, delete-orphan")
    vacaciones          = relationship("FichaVacacion", back_populates="trabajador", cascade="all, delete-orphan")
    permisos            = relationship("FichaPermiso", back_populates="trabajador", cascade="all, delete-orphan")
    prestamos_rrhh      = relationship("FichaPrestamo", back_populates="trabajador", cascade="all, delete-orphan")
    cargos_desempenados = relationship("CargoDesempenado", back_populates="trabajador", cascade="all, delete-orphan")
    observaciones       = relationship("Observacion", back_populates="trabajador", cascade="all, delete-orphan")
    eval_cuantitativas  = relationship("TrabajadorEvalCuantitativa", back_populates="trabajador", cascade="all, delete-orphan")
    eval_cualitativas   = relationship("TrabajadorEvalCualitativa", back_populates="trabajador", cascade="all, delete-orphan")
    contratos_rrhh      = relationship("ContratoRrhh", back_populates="trabajador", cascade="all, delete-orphan")

    @property
    def nombre_completo(self) -> str:
        partes = [self.apellido_paterno]
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        partes.append(self.nombres)
        return " ".join(partes)


class TrabajadorApv(Base):
    """APV individual y colectivo por trabajador (cap. 4.4.3 — Detalle APV)."""
    __tablename__ = "trabajador_apv"
    __table_args__ = (
        Index("ix_apv_trabajador", "trabajador_id"),
        {"schema": "rrhh"},
    )

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id          = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id      = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    tipo_apv           = Column(String(10), nullable=False)   # 'normal' | 'colectivo'
    moneda_trabajador  = Column(String(5), nullable=False, default="CLP")
    monto_trabajador   = Column(Numeric(12, 4), nullable=False, default=0)
    moneda_empleador   = Column(String(5))
    monto_empleador    = Column(Numeric(12, 4), nullable=False, default=0)
    administra_afp     = Column(Boolean, nullable=False, default=True)
    afp_id             = Column(Integer, ForeignKey("nomina.afp.id"))
    otra_institucion   = Column(String(100))
    rebaja_art42bis    = Column(Boolean, nullable=False, default=False)
    fecha_inicio       = Column(Date, nullable=False)
    fecha_termino      = Column(Date)
    es_activo          = Column(Boolean, nullable=False, default=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    trabajador = relationship("Trabajador", back_populates="apvs")
    # afp: acceder via join explícito a nomina.afp


class TrabajadorConyugeAfiliado(Base):
    """Cónyuge como afiliado voluntario AFP (Ley 20.255, cap. 4.4.3)."""
    __tablename__ = "trabajador_conyuge_afiliado"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trabajador_id"),
        {"schema": "rrhh"},
    )

    id                       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id                = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id            = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    rut_conyuge              = Column(String(12), nullable=False)
    nombres                  = Column(String(200), nullable=False)
    afp_id                   = Column(Integer, ForeignKey("nomina.afp.id"))
    monto_cotiz_voluntaria   = Column(Numeric(12, 2), nullable=False, default=0)
    monto_deposito_ahorro    = Column(Numeric(12, 2), nullable=False, default=0)
    fecha_inicio             = Column(Date, nullable=False)
    fecha_termino            = Column(Date)
    cesar_cotizacion         = Column(Boolean, nullable=False, default=False)
    created_at               = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="conyuge_afiliado")
    # afp: acceder via join explícito a nomina.afp


class CargaFamiliar(Base):
    """Cargas familiares del trabajador (cap. 4.4.4)."""
    __tablename__ = "carga_familiar"
    __table_args__ = (
        Index("ix_carga_familiar_trabajador", "trabajador_id"),
        Index("ix_carga_familiar_tenant", "tenant_id"),
        {"schema": "rrhh"},
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    rut              = Column(String(12), nullable=False)
    nombres          = Column(String(200), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    tipo_carga       = Column(String(10), nullable=False)   # simple/maternal/invalidez
    parentesco       = Column(String(15), nullable=False)   # hijo/conyuge/progenitor/hermano
    es_activa        = Column(Boolean, nullable=False, default=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False)

    trabajador = relationship("Trabajador", back_populates="cargas_familiares")


class CargaFamiliarSueldoMensual(Base):
    """Sueldo imponible mensual para cálculo proporcional asignación familiar (cap. 4.4.4)."""
    __tablename__ = "carga_familiar_sueldo_mensual"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trabajador_id", "anio", "mes"),
        {"schema": "rrhh"},
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    anio             = Column(SmallInteger, nullable=False)
    mes              = Column(SmallInteger, nullable=False)
    sueldo_imponible = Column(Numeric(12, 2), nullable=False, default=0)


class FichaVacacion(Base):
    """Registro de vacaciones otorgadas/utilizadas (cap. 8.3.1, 8.9.1)."""
    __tablename__ = "ficha_vacacion"
    __table_args__ = (
        Index("ix_ficha_vacacion_trabajador", "trabajador_id"),
        Index("ix_ficha_vacacion_tenant", "tenant_id"),
        {"schema": "rrhh"},
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id   = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evento    = Column(Date, nullable=False)
    descripcion     = Column(String(200))
    fecha_desde     = Column(Date, nullable=False)
    fecha_hasta     = Column(Date, nullable=False)
    dias_otorgados  = Column(Numeric(5, 2), nullable=False, default=0)
    dias_utilizados = Column(Numeric(5, 2), nullable=False, default=0)
    es_progresiva   = Column(Boolean, nullable=False, default=False)
    comprobante_path = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="vacaciones")


class FichaPermiso(Base):
    """Permisos otorgados al trabajador (cap. 8.3.2)."""
    __tablename__ = "ficha_permiso"
    __table_args__ = (
        Index("ix_ficha_permiso_trabajador", "trabajador_id"),
        {"schema": "rrhh"},
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id   = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evento    = Column(Date, nullable=False)
    tipo_permiso_id = Column(UUID(as_uuid=True), ForeignKey("rrhh.tipo_permiso.id"), nullable=False)
    fecha_desde     = Column(Date, nullable=False)
    fecha_hasta     = Column(Date, nullable=False)
    dias_otorgados  = Column(Numeric(5, 2), nullable=False, default=0)
    observaciones   = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador   = relationship("Trabajador", back_populates="permisos")
    tipo_permiso = relationship("TipoPermiso")


class FichaPrestamo(Base):
    """Registro histórico RRHH de préstamos (cap. 8.3.3)."""
    __tablename__ = "ficha_prestamo"
    __table_args__ = {"schema": "rrhh"}

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evento  = Column(Date, nullable=False)
    tipo          = Column(String(10), nullable=False)   # 'otorgado' | 'abono'
    monto         = Column(Numeric(12, 2), nullable=False, default=0)
    comentario    = Column(Text)
    prestamo_id   = Column(UUID(as_uuid=True))           # referencia a nomina.prestamo
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="prestamos_rrhh")


class CargoDesempenado(Base):
    """Historial de cargos desempeñados por el trabajador (cap. 8.3.4)."""
    __tablename__ = "cargo_desempenado"
    __table_args__ = {"schema": "rrhh"}

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id         = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id     = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    cargo_id          = Column(UUID(as_uuid=True), ForeignKey("nomina.cargo.id"))
    cargo_descripcion = Column(String(100))   # texto libre si no existe en catálogo
    fecha_desde       = Column(Date, nullable=False)
    fecha_hasta       = Column(Date)
    observaciones     = Column(Text)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="cargos_desempenados")
    # cargo: acceder via join explícito a nomina.cargo


class Observacion(Base):
    """Observaciones generales del trabajador (cap. 8.3.5)."""
    __tablename__ = "observacion"
    __table_args__ = {"schema": "rrhh"}

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evento  = Column(Date, nullable=False)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("rrhh.supervisor.id"))
    tipo          = Column(String(50))
    descripcion   = Column(Text, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="observaciones")
    supervisor = relationship("Supervisor")


class TrabajadorEvalCuantitativa(Base):
    """Evaluaciones cuantitativas del trabajador (cap. 8.3.7, 8.4)."""
    __tablename__ = "trabajador_eval_cuantitativa"
    __table_args__ = {"schema": "rrhh"}

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evaluacion = Column(Date, nullable=False)
    evaluacion_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.evaluacion_cuantitativa.id"), nullable=False)
    atributo_id      = Column(UUID(as_uuid=True), ForeignKey("rrhh.atributo_eval_cuantitativa.id"), nullable=False)
    valor            = Column(Numeric(6, 2), nullable=False)
    observaciones    = Column(Text)
    creado_por_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="eval_cuantitativas")
    evaluacion = relationship("EvaluacionCuantitativa")
    atributo   = relationship("AtributoEvalCuantitativa")


class TrabajadorEvalCualitativa(Base):
    """Evaluaciones cualitativas del trabajador (cap. 8.3.8, 8.7)."""
    __tablename__ = "trabajador_eval_cualitativa"
    __table_args__ = {"schema": "rrhh"}

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evaluacion = Column(Date, nullable=False)
    evaluacion_id    = Column(UUID(as_uuid=True), ForeignKey("rrhh.evaluacion_cualitativa.id"), nullable=False)
    atributo_id      = Column(UUID(as_uuid=True), ForeignKey("rrhh.atributo_eval_cualitativa.id"), nullable=False)
    descripcion      = Column(Text)
    creado_por_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="eval_cualitativas")
    evaluacion = relationship("EvaluacionCualitativa")
    atributo   = relationship("AtributoEvalCualitativa")


class ContratoRrhh(Base):
    """Vista histórica RRHH de contratos (cap. 8.3.9)."""
    __tablename__ = "contrato_rrhh"
    __table_args__ = {"schema": "rrhh"}

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("rrhh.trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_evento  = Column(Date, nullable=False)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("rrhh.supervisor.id"))
    contrato_id   = Column(UUID(as_uuid=True))    # referencia a nomina.contrato (sin FK dura por cross-schema)
    descripcion   = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trabajador = relationship("Trabajador", back_populates="contratos_rrhh")
    supervisor = relationship("Supervisor")