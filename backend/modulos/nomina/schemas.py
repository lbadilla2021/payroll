"""
modulos/nomina/schemas.py
=========================
Schemas Pydantic v2 para el módulo Nómina.

Iteración 2: catálogos globales (AFP, Isapre, CCAF, Mutualidad, Banco,
Región, Comuna, TipoMoneda, Tramos, Factores) + tablas operacionales
por tenant (EmpresaConfig, Sucursal, CentroCosto, Cargo, TipoContrato,
CausalFiniquito, ClausulaAdicional, ConceptoRemuneracion, ParametroMensual).

Convención de acceso:
- Catálogos globales → sin tenant_id en schemas de entrada/salida.
- Operacionales → tenant_id se extrae del token, nunca del body.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# AFP
# ─────────────────────────────────────────────────────────────────────────────

class AfpRead(BaseModel):
    id:                  int
    codigo_previred:     int
    nombre:              str
    nombre_corto:        str
    tasa_trabajador:     Decimal
    tasa_sis:            Decimal
    tasa_trabajo_pesado: Decimal
    es_activa:           bool

    model_config = ConfigDict(from_attributes=True)


class AfpUpdate(BaseModel):
    """Solo superadmin puede actualizar tasas."""
    tasa_trabajador:     Optional[Decimal] = Field(None, ge=0, le=1)
    tasa_sis:            Optional[Decimal] = Field(None, ge=0, le=1)
    tasa_trabajo_pesado: Optional[Decimal] = Field(None, ge=0, le=1)
    es_activa:           Optional[bool]    = None


# ─────────────────────────────────────────────────────────────────────────────
# ISAPRE
# ─────────────────────────────────────────────────────────────────────────────

class IsapreRead(BaseModel):
    id:              int
    codigo_previred: int
    nombre:          str
    nombre_corto:    str
    es_activa:       bool

    model_config = ConfigDict(from_attributes=True)


class IsapreUpdate(BaseModel):
    es_activa: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# CCAF
# ─────────────────────────────────────────────────────────────────────────────

class CcafRead(BaseModel):
    id:           int
    codigo:       str
    nombre:       str
    nombre_corto: str
    es_activa:    bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# MUTUALIDAD
# ─────────────────────────────────────────────────────────────────────────────

class MutualidadRead(BaseModel):
    id:              int
    codigo:          str
    nombre:          str
    nombre_corto:    str
    tasa_cotizacion: Decimal
    es_activa:       bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# BANCO
# ─────────────────────────────────────────────────────────────────────────────

class BancoRead(BaseModel):
    id:        int
    codigo:    int
    nombre:    str
    es_activo: bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# TIPO MOVIMIENTO BANCARIO
# ─────────────────────────────────────────────────────────────────────────────

class TipoMovimientoBancarioRead(BaseModel):
    id:          int
    descripcion: str

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# REGIÓN
# ─────────────────────────────────────────────────────────────────────────────

class RegionRead(BaseModel):
    id:              int
    codigo:          str
    nombre:          str
    es_zona_extrema: bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# COMUNA
# ─────────────────────────────────────────────────────────────────────────────

class ComunaRead(BaseModel):
    codigo:    int
    nombre:    str
    region_id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# TIPO MONEDA
# ─────────────────────────────────────────────────────────────────────────────

class TipoMonedaRead(BaseModel):
    id:          int
    codigo:      str
    descripcion: str
    es_activa:   bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# TRAMOS ASIGNACIÓN FAMILIAR
# ─────────────────────────────────────────────────────────────────────────────

class TramoAsignacionFamiliarRead(BaseModel):
    id:          int
    anio:        int
    mes:         int
    tramo:       int
    renta_desde: Decimal
    renta_hasta: Optional[Decimal]
    valor_carga: Decimal
    descripcion: str

    model_config = ConfigDict(from_attributes=True)


class TramoAsignacionFamiliarCreate(BaseModel):
    """Superadmin: actualización anual de tramos."""
    anio:        int     = Field(..., ge=2020, le=2100)
    mes:         int     = Field(..., ge=1, le=12)
    tramo:       int     = Field(..., ge=1, le=4)
    renta_desde: Decimal = Field(..., ge=0)
    renta_hasta: Optional[Decimal] = None
    valor_carga: Decimal = Field(..., ge=0)
    descripcion: str     = Field(..., max_length=50)


# ─────────────────────────────────────────────────────────────────────────────
# TRAMOS IMPUESTO ÚNICO UTM
# ─────────────────────────────────────────────────────────────────────────────

class TramoImpuestoUnicoRead(BaseModel):
    id:         int
    anio:       int
    mes:        int
    orden:      int
    utm_desde:  Decimal
    utm_hasta:  Optional[Decimal]
    tasa:       Decimal
    rebaja_utm: Decimal

    model_config = ConfigDict(from_attributes=True)


class TramoImpuestoUnicoCreate(BaseModel):
    """Superadmin: actualización anual de tramos SII."""
    anio:       int     = Field(..., ge=2020, le=2100)
    mes:        int     = Field(..., ge=1, le=12)
    orden:      int     = Field(..., ge=1, le=20)
    utm_desde:  Decimal = Field(..., ge=0)
    utm_hasta:  Optional[Decimal] = None
    tasa:       Decimal = Field(..., ge=0, le=1)
    rebaja_utm: Decimal = Field(..., ge=0)


# ─────────────────────────────────────────────────────────────────────────────
# FACTOR ACTUALIZACIÓN (UTM / UF / IMM)
# ─────────────────────────────────────────────────────────────────────────────

class FactorActualizacionRead(BaseModel):
    id:     int
    anio:   int
    mes:    int
    utm:    Decimal
    uf:     Decimal
    factor: Decimal
    imm:    Decimal

    model_config = ConfigDict(from_attributes=True)


class FactorActualizacionCreate(BaseModel):
    """Ingreso mensual de UTM/UF/IMM — superadmin o proceso automático."""
    anio:   int     = Field(..., ge=2020, le=2100)
    mes:    int     = Field(..., ge=1, le=12)
    utm:    Decimal = Field(..., gt=0)
    uf:     Decimal = Field(..., gt=0)
    factor: Decimal = Field(Decimal("1.0"), gt=0)
    imm:    Decimal = Field(..., gt=0)


class FactorActualizacionUpdate(BaseModel):
    utm:    Optional[Decimal] = Field(None, gt=0)
    uf:     Optional[Decimal] = Field(None, gt=0)
    factor: Optional[Decimal] = Field(None, gt=0)
    imm:    Optional[Decimal] = Field(None, gt=0)


# ─────────────────────────────────────────────────────────────────────────────
# SERVICIO MÉDICO CCHC
# ─────────────────────────────────────────────────────────────────────────────

class ServMedCchcRead(BaseModel):
    id:          int
    anio:        int
    mes:         int
    porcentaje:  Decimal
    tope_uf:     Decimal
    valor_carga: Decimal

    model_config = ConfigDict(from_attributes=True)


class ServMedCchcCreate(BaseModel):
    anio:        int     = Field(..., ge=2020, le=2100)
    mes:         int     = Field(..., ge=1, le=12)
    porcentaje:  Decimal = Field(..., ge=0, le=1)
    tope_uf:     Decimal = Field(..., ge=0)
    valor_carga: Decimal = Field(Decimal("0"), ge=0)


class ServMedCchcUpdate(BaseModel):
    porcentaje:  Optional[Decimal] = Field(None, ge=0, le=1)
    tope_uf:     Optional[Decimal] = Field(None, ge=0)
    valor_carga: Optional[Decimal] = Field(None, ge=0)


# ─────────────────────────────────────────────────────────────────────────────
# EMPRESA CONFIG (operacional por tenant)
# ─────────────────────────────────────────────────────────────────────────────

class EmpresaConfigRead(BaseModel):
    id:                     UUID
    tenant_id:              UUID
    nombre_rep_legal:       Optional[str]
    rut_rep_legal:          Optional[str]
    nombre_contador:        Optional[str]
    rut_contador:           Optional[str]
    giro:                   Optional[str]
    ccaf_id:                Optional[int]
    mutualidad_id:          Optional[int]
    modalidad_gratificacion: str
    logo_url:               Optional[str]
    numero_convenio_fun:    Optional[str]
    mapi_nombre_remitente:  Optional[str]
    mapi_email_remitente:   Optional[str]
    created_at:             datetime
    updated_at:             datetime

    model_config = ConfigDict(from_attributes=True)


class EmpresaConfigCreate(BaseModel):
    nombre_rep_legal:       Optional[str] = Field(None, max_length=200)
    rut_rep_legal:          Optional[str] = Field(None, max_length=12)
    nombre_contador:        Optional[str] = Field(None, max_length=200)
    rut_contador:           Optional[str] = Field(None, max_length=12)
    giro:                   Optional[str] = Field(None, max_length=200)
    ccaf_id:                Optional[int] = None
    mutualidad_id:          Optional[int] = None
    modalidad_gratificacion: str = Field("calculada")
    logo_url:               Optional[str] = None
    numero_convenio_fun:    Optional[str] = Field(None, max_length=50)
    mapi_nombre_remitente:  Optional[str] = Field(None, max_length=100)
    mapi_email_remitente:   Optional[str] = Field(None, max_length=254)

    @field_validator("modalidad_gratificacion")
    @classmethod
    def validar_modalidad(cls, v):
        opciones = {"calculada", "informada", "proporcional", "calculada_dict4232", "no_paga"}
        if v not in opciones:
            raise ValueError(f"Debe ser uno de: {opciones}")
        return v


class EmpresaConfigUpdate(BaseModel):
    nombre_rep_legal:       Optional[str] = Field(None, max_length=200)
    rut_rep_legal:          Optional[str] = Field(None, max_length=12)
    nombre_contador:        Optional[str] = Field(None, max_length=200)
    rut_contador:           Optional[str] = Field(None, max_length=12)
    giro:                   Optional[str] = Field(None, max_length=200)
    ccaf_id:                Optional[int] = None
    mutualidad_id:          Optional[int] = None
    modalidad_gratificacion: Optional[str] = None
    logo_url:               Optional[str] = None
    numero_convenio_fun:    Optional[str] = Field(None, max_length=50)
    mapi_nombre_remitente:  Optional[str] = Field(None, max_length=100)
    mapi_email_remitente:   Optional[str] = Field(None, max_length=254)


# ─────────────────────────────────────────────────────────────────────────────
# SUCURSAL
# ─────────────────────────────────────────────────────────────────────────────

class SucursalCreate(BaseModel):
    codigo:          str  = Field(..., min_length=1, max_length=20)
    nombre:          str  = Field(..., min_length=2, max_length=100)
    direccion:       Optional[str]  = Field(None, max_length=200)
    region_id:       Optional[int]  = None
    comuna_id:       Optional[int]  = None
    codigo_pais:     Optional[str]  = Field("CL", max_length=5)
    telefono:        Optional[str]  = Field(None, max_length=30)
    codigo_previred: Optional[str]  = Field(None, max_length=20)
    es_activa:       bool           = True


class SucursalUpdate(BaseModel):
    nombre:          Optional[str]  = Field(None, min_length=2, max_length=100)
    direccion:       Optional[str]  = Field(None, max_length=200)
    region_id:       Optional[int]  = None
    comuna_id:       Optional[int]  = None
    telefono:        Optional[str]  = Field(None, max_length=30)
    codigo_previred: Optional[str]  = Field(None, max_length=20)
    es_activa:       Optional[bool] = None


class SucursalRead(BaseModel):
    id:              UUID
    tenant_id:       UUID
    codigo:          str
    nombre:          str
    direccion:       Optional[str]
    region_id:       Optional[int]
    comuna_id:       Optional[int]
    codigo_pais:     Optional[str]
    telefono:        Optional[str]
    codigo_previred: Optional[str]
    es_activa:       bool
    created_at:      datetime
    updated_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class SucursalList(BaseModel):
    items: list[SucursalRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# CENTRO DE COSTO
# ─────────────────────────────────────────────────────────────────────────────

class CentroCostoCreate(BaseModel):
    codigo:          str  = Field(..., min_length=1, max_length=20)
    descripcion:     str  = Field(..., min_length=2, max_length=100)
    codigo_previred: Optional[str]  = Field(None, max_length=20)
    es_activo:       bool           = True


class CentroCostoUpdate(BaseModel):
    descripcion:     Optional[str]  = Field(None, min_length=2, max_length=100)
    codigo_previred: Optional[str]  = Field(None, max_length=20)
    es_activo:       Optional[bool] = None


class CentroCostoRead(BaseModel):
    id:              UUID
    tenant_id:       UUID
    codigo:          str
    descripcion:     str
    codigo_previred: Optional[str]
    es_activo:       bool
    created_at:      datetime
    updated_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class CentroCostoList(BaseModel):
    items: list[CentroCostoRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# CARGO
# ─────────────────────────────────────────────────────────────────────────────

class CargoCreate(BaseModel):
    codigo:      str  = Field(..., min_length=1, max_length=20)
    descripcion: str  = Field(..., min_length=2, max_length=100)
    es_activo:   bool = True


class CargoUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, min_length=2, max_length=100)
    es_activo:   Optional[bool] = None


class CargoRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    es_activo:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class CargoList(BaseModel):
    items: list[CargoRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# TIPO CONTRATO
# ─────────────────────────────────────────────────────────────────────────────

class TipoContratoCreate(BaseModel):
    codigo:      str  = Field(..., min_length=1, max_length=20)
    descripcion: str  = Field(..., min_length=2, max_length=100)
    es_activo:   bool = True


class TipoContratoUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, min_length=2, max_length=100)
    es_activo:   Optional[bool] = None


class TipoContratoRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    es_activo:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class TipoContratoList(BaseModel):
    items: list[TipoContratoRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# CAUSAL FINIQUITO
# ─────────────────────────────────────────────────────────────────────────────

class CausalFiniquitoCreate(BaseModel):
    codigo:      str           = Field(..., min_length=1, max_length=20)
    descripcion: str           = Field(..., min_length=2, max_length=200)
    articulo:    Optional[str] = Field(None, max_length=50)
    es_activa:   bool          = True


class CausalFiniquitoUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, min_length=2, max_length=200)
    articulo:    Optional[str]  = Field(None, max_length=50)
    es_activa:   Optional[bool] = None


class CausalFiniquitoRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    articulo:    Optional[str]
    es_activa:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class CausalFiniquitoList(BaseModel):
    items: list[CausalFiniquitoRead]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# CLÁUSULA ADICIONAL
# ─────────────────────────────────────────────────────────────────────────────

class ClausulaAdicionalCreate(BaseModel):
    codigo:      str  = Field(..., min_length=1, max_length=20)
    descripcion: str  = Field(..., min_length=2, max_length=200)
    texto:       str  = Field(..., min_length=1)
    es_activa:   bool = True


class ClausulaAdicionalUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, min_length=2, max_length=200)
    texto:       Optional[str]  = None
    es_activa:   Optional[bool] = None


class ClausulaAdicionalRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    texto:       str
    es_activa:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class ClausulaAdicionalList(BaseModel):
    items: list[ClausulaAdicionalRead]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# CONCEPTO REMUNERACIÓN (Haberes y Descuentos)
# ─────────────────────────────────────────────────────────────────────────────

class ConceptoRemuneracionCreate(BaseModel):
    codigo:      str = Field(..., min_length=1, max_length=10)
    descripcion: str = Field(..., min_length=2, max_length=100)
    tipo:        str = Field(..., pattern=r"^[HD]$")  # H=Haber, D=Descuento

    # Propiedades tributarias/previsionales
    es_imponible:       bool = True
    es_tributable:      bool = True
    es_renta_exenta:    bool = False
    reliquida_impuesto: bool = False

    # Propiedades de cálculo
    es_fijo:                bool = True
    es_valor_diario:        bool = False
    es_semana_corrida:      bool = False
    es_porcentaje:          bool = False
    es_adicional_horas_ext: bool = False
    es_horas_extras:        bool = False
    adiciona_sueldo_imm:    bool = False
    es_haber_variable:      bool = False

    # Descuentos especiales
    es_anticipo:      bool = False
    es_prestamo_ccaf: bool = False
    es_prestamo:      bool = False

    # LRE
    clasificacion_lre: Optional[str] = Field(None, max_length=50)
    exportable_lre:    bool           = False


class ConceptoRemuneracionUpdate(BaseModel):
    descripcion:            Optional[str]  = Field(None, min_length=2, max_length=100)
    es_imponible:           Optional[bool] = None
    es_tributable:          Optional[bool] = None
    es_renta_exenta:        Optional[bool] = None
    reliquida_impuesto:     Optional[bool] = None
    es_fijo:                Optional[bool] = None
    es_valor_diario:        Optional[bool] = None
    es_semana_corrida:      Optional[bool] = None
    es_porcentaje:          Optional[bool] = None
    es_adicional_horas_ext: Optional[bool] = None
    es_horas_extras:        Optional[bool] = None
    adiciona_sueldo_imm:    Optional[bool] = None
    es_haber_variable:      Optional[bool] = None
    es_anticipo:            Optional[bool] = None
    es_prestamo_ccaf:       Optional[bool] = None
    es_prestamo:            Optional[bool] = None
    clasificacion_lre:      Optional[str]  = Field(None, max_length=50)
    exportable_lre:         Optional[bool] = None
    es_activo:              Optional[bool] = None


class ConceptoRemuneracionRead(BaseModel):
    id:                     UUID
    tenant_id:              UUID
    codigo:                 str
    descripcion:            str
    tipo:                   str
    es_imponible:           bool
    es_tributable:          bool
    es_renta_exenta:        bool
    reliquida_impuesto:     bool
    es_fijo:                bool
    es_valor_diario:        bool
    es_semana_corrida:      bool
    es_porcentaje:          bool
    es_adicional_horas_ext: bool
    es_horas_extras:        bool
    adiciona_sueldo_imm:    bool
    es_haber_variable:      bool
    es_anticipo:            bool
    es_prestamo_ccaf:       bool
    es_prestamo:            bool
    clasificacion_lre:      Optional[str]
    exportable_lre:         bool
    es_activo:              bool
    created_at:             datetime
    updated_at:             datetime

    model_config = ConfigDict(from_attributes=True)


class ConceptoRemuneracionList(BaseModel):
    items: list[ConceptoRemuneracionRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# PARÁMETRO MENSUAL
# ─────────────────────────────────────────────────────────────────────────────

class ParametroMensualCreate(BaseModel):
    anio:                int     = Field(..., ge=2020, le=2100)
    mes:                 int     = Field(..., ge=1, le=12)
    utm:                 Decimal = Field(..., gt=0)
    uf:                  Decimal = Field(..., gt=0)
    imm:                 Decimal = Field(..., gt=0)
    factor_actualizacion: Decimal = Field(Decimal("1.0"), gt=0)
    tope_imponible_afp:  Decimal = Field(..., gt=0)
    tope_imponible_salud: Decimal = Field(..., gt=0)
    tope_seg_cesantia:   Decimal = Field(..., gt=0)
    tasa_acc_trabajo:    Decimal = Field(Decimal("0.0093"), ge=0, le=1)
    tasa_apv_colectivo:  Decimal = Field(Decimal("0"), ge=0, le=1)


class ParametroMensualUpdate(BaseModel):
    utm:                  Optional[Decimal] = Field(None, gt=0)
    uf:                   Optional[Decimal] = Field(None, gt=0)
    imm:                  Optional[Decimal] = Field(None, gt=0)
    factor_actualizacion: Optional[Decimal] = Field(None, gt=0)
    tope_imponible_afp:   Optional[Decimal] = Field(None, gt=0)
    tope_imponible_salud: Optional[Decimal] = Field(None, gt=0)
    tope_seg_cesantia:    Optional[Decimal] = Field(None, gt=0)
    tasa_acc_trabajo:     Optional[Decimal] = Field(None, ge=0, le=1)
    tasa_apv_colectivo:   Optional[Decimal] = Field(None, ge=0, le=1)
    bloqueado:            Optional[bool]    = None


class ParametroMensualRead(BaseModel):
    id:                   UUID
    tenant_id:            UUID
    anio:                 int
    mes:                  int
    utm:                  Decimal
    uf:                   Decimal
    imm:                  Decimal
    factor_actualizacion: Decimal
    tope_imponible_afp:   Decimal
    tope_imponible_salud: Decimal
    tope_seg_cesantia:    Decimal
    tasa_acc_trabajo:     Decimal
    tasa_apv_colectivo:   Decimal
    bloqueado:            bool
    cerrado:              bool
    fecha_cierre:         Optional[datetime]
    created_at:           datetime
    updated_at:           datetime

    model_config = ConfigDict(from_attributes=True)


class ParametroMensualList(BaseModel):
    items: list[ParametroMensualRead]
    total: int
    page:  int
    size:  int
