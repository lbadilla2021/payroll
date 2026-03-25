"""
modulos/rrhh/schemas.py
=======================
Schemas Pydantic v2 para el módulo RRHH.
Patrón: XxxCreate (entrada), XxxUpdate (patch), XxxRead (salida), XxxList (listado resumido).
"""

import re
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _validate_rut(rut: str) -> str:
    """Valida formato RUT chileno: 12345678-9 o 12345678-K."""
    rut = rut.strip().upper()
    if not re.match(r"^\d{7,8}-[\dK]$", rut):
        raise ValueError("RUT inválido. Formato esperado: 12345678-9")
    return rut


# ─────────────────────────────────────────────────────────────────────────────
# SUPERVISORES
# ─────────────────────────────────────────────────────────────────────────────

class SupervisorCreate(BaseModel):
    codigo:     str = Field(..., min_length=1, max_length=20)
    nombre:     str = Field(..., min_length=2, max_length=200)
    es_activo:  bool = True


class SupervisorUpdate(BaseModel):
    nombre:    Optional[str]  = Field(None, min_length=2, max_length=200)
    es_activo: Optional[bool] = None


class SupervisorRead(BaseModel):
    id:         UUID
    tenant_id:  UUID
    codigo:     str
    nombre:     str
    es_activo:  bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupervisorList(BaseModel):
    items: list[SupervisorRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE PERMISO
# ─────────────────────────────────────────────────────────────────────────────

class TipoPermisoCreate(BaseModel):
    codigo:      str = Field(..., min_length=1, max_length=20)
    descripcion: str = Field(..., min_length=2, max_length=100)
    es_activo:   bool = True


class TipoPermisoUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, min_length=2, max_length=100)
    es_activo:   Optional[bool] = None


class TipoPermisoRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    es_activo:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class TipoPermisoList(BaseModel):
    items: list[TipoPermisoRead]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIONES CUANTITATIVAS
# ─────────────────────────────────────────────────────────────────────────────

class AtributoEvalCuantitativaCreate(BaseModel):
    codigo:      str = Field(..., min_length=1, max_length=30)
    descripcion: str = Field(..., min_length=2, max_length=200)
    es_activo:   bool = True


class AtributoEvalCuantitativaUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, max_length=200)
    es_activo:   Optional[bool] = None


class AtributoEvalCuantitativaRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    es_activo:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluacionCuantitativaCreate(BaseModel):
    codigo:      str   = Field(..., min_length=1, max_length=20)
    descripcion: str   = Field(..., min_length=2, max_length=100)
    valor_min:   float = Field(0, ge=0)
    valor_max:   float = Field(100, ge=0)
    es_activa:   bool  = True

    @model_validator(mode="after")
    def rango_valido(self):
        if self.valor_min >= self.valor_max:
            raise ValueError("valor_min debe ser menor que valor_max")
        return self


class EvaluacionCuantitativaUpdate(BaseModel):
    descripcion: Optional[str]   = Field(None, max_length=100)
    valor_min:   Optional[float] = None
    valor_max:   Optional[float] = None
    es_activa:   Optional[bool]  = None


class EvaluacionCuantitativaRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    valor_min:   float
    valor_max:   float
    es_activa:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIONES CUALITATIVAS
# ─────────────────────────────────────────────────────────────────────────────

class AtributoEvalCualitativaCreate(BaseModel):
    codigo:      str = Field(..., min_length=1, max_length=30)
    descripcion: str = Field(..., min_length=2, max_length=200)
    es_activo:   bool = True


class AtributoEvalCualitativaUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, max_length=200)
    es_activo:   Optional[bool] = None


class AtributoEvalCualitativaRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    es_activo:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluacionCualitativaCreate(BaseModel):
    codigo:      str = Field(..., min_length=1, max_length=20)
    descripcion: str = Field(..., min_length=2, max_length=100)
    es_activa:   bool = True


class EvaluacionCualitativaUpdate(BaseModel):
    descripcion: Optional[str]  = Field(None, max_length=100)
    es_activa:   Optional[bool] = None


class EvaluacionCualitativaRead(BaseModel):
    id:          UUID
    tenant_id:   UUID
    codigo:      str
    descripcion: str
    es_activa:   bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# TRABAJADOR
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorCreate(BaseModel):
    codigo:           str = Field(..., min_length=1, max_length=20)

    # Datos personales
    rut:              str = Field(..., min_length=9, max_length=12)
    nombres:          str = Field(..., min_length=1, max_length=100)
    apellido_paterno: str = Field(..., min_length=1, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[date] = None
    email:            Optional[str]  = Field(None, max_length=254)
    codigo_pais:      Optional[str]  = Field("CL", max_length=5)
    telefono:         Optional[str]  = Field(None, max_length=30)
    direccion_calle:  Optional[str]  = Field(None, max_length=200)
    direccion_numero: Optional[str]  = Field(None, max_length=20)
    region_id:        Optional[int]  = None
    comuna_id:        Optional[int]  = None
    estado_civil:     Optional[int]  = Field(None, ge=1, le=4)
    sexo:             Optional[str]  = Field(None, pattern=r"^[MF]$")
    es_extranjero:    bool            = False
    nacionalidad:     Optional[str]  = Field(None, max_length=60)

    # Datos laborales
    tipo_sueldo:      str   = Field("M", pattern=r"^[MDHE]$")
    moneda_id:        int   = 1
    monto_sueldo:     float = Field(0, ge=0)
    horas_semana:     Optional[float] = Field(None, ge=0, le=60)
    dias_semana:      Optional[int]   = Field(None, ge=1, le=7)

    tipo_gratificacion:  str   = Field("calculada")
    monto_gratificacion: Optional[float] = Field(None, ge=0)

    monto_movilizacion: float = Field(0, ge=0)
    monto_colacion:     float = Field(0, ge=0)

    forma_pago:        str           = Field("E", pattern=r"^[ECDP]$")
    banco_id:          Optional[int] = None
    nro_cuenta:        Optional[str] = Field(None, max_length=30)
    tipo_mov_bancario: Optional[int] = None

    impuesto_agricola:        bool  = False
    art61_ley18768:           bool  = False
    pct_asignacion_zona:      float = Field(0, ge=0, le=100)
    incrementa_pct_zona:      bool  = False
    no_calcula_ajuste_sueldo: bool  = False

    fecha_contrato:   Optional[date] = None
    profesion:        Optional[str]  = Field(None, max_length=100)
    labor:            Optional[str]  = Field(None, max_length=200)
    cargo_id:         Optional[UUID] = None
    sucursal_id:      Optional[UUID] = None
    centro_costo_id:  Optional[UUID] = None
    supervisor_id:    Optional[UUID] = None
    tipo_contrato_id: Optional[UUID] = None

    # Datos previsionales
    regimen_previsional:       int           = Field(1, ge=1, le=4)
    afp_id:                    Optional[int] = None
    cotizacion_voluntaria_afp: float         = Field(0, ge=0)
    rebaja_imp_cotiz_vol:      bool          = False

    regimen_salud:      str   = Field("FONASA", pattern=r"^(FONASA|ISAPRE)$")
    isapre_id:          Optional[int]   = None
    modalidad_isapre:   Optional[int]   = Field(None, ge=1, le=6)
    monto_isapre_pesos: float           = Field(0, ge=0)
    monto_isapre_uf:    float           = Field(0, ge=0)

    tiene_seg_cesantia:  bool          = True
    contrato_plazo_fijo: bool          = False
    fecha_ingreso_sc:    Optional[date] = None
    fecha_ultimo_mes_sc: Optional[date] = None
    afp_seg_cesantia_id: Optional[int] = None
    no_cotiza_sis:       bool          = False

    beneficiarios_ges: int           = Field(0, ge=0)
    vigencia_ges:      Optional[int] = Field(None, ge=0, le=1)

    tiene_serv_med_cchc: bool = False
    tipo_trabajador:     int  = Field(1, ge=1, le=4)

    @field_validator("rut")
    @classmethod
    def validar_rut(cls, v):
        return _validate_rut(v)

    @field_validator("tipo_gratificacion")
    @classmethod
    def validar_gratificacion(cls, v):
        opciones = {"calculada", "informada", "proporcional", "calculada_dict4232", "no_paga"}
        if v not in opciones:
            raise ValueError(f"tipo_gratificacion debe ser uno de: {opciones}")
        return v


class TrabajadorUpdate(BaseModel):
    """Todos los campos opcionales para PATCH."""
    nombres:          Optional[str]   = Field(None, max_length=100)
    apellido_paterno: Optional[str]   = Field(None, max_length=100)
    apellido_materno: Optional[str]   = Field(None, max_length=100)
    fecha_nacimiento: Optional[date]  = None
    email:            Optional[str]   = Field(None, max_length=254)
    telefono:         Optional[str]   = Field(None, max_length=30)
    direccion_calle:  Optional[str]   = Field(None, max_length=200)
    direccion_numero: Optional[str]   = Field(None, max_length=20)
    region_id:        Optional[int]   = None
    comuna_id:        Optional[int]   = None
    estado_civil:     Optional[int]   = Field(None, ge=1, le=4)
    sexo:             Optional[str]   = Field(None, pattern=r"^[MF]$")
    es_extranjero:    Optional[bool]  = None
    nacionalidad:     Optional[str]   = Field(None, max_length=60)

    tipo_sueldo:         Optional[str]   = Field(None, pattern=r"^[MDHE]$")
    moneda_id:           Optional[int]   = None
    monto_sueldo:        Optional[float] = Field(None, ge=0)
    horas_semana:        Optional[float] = Field(None, ge=0, le=60)
    dias_semana:         Optional[int]   = Field(None, ge=1, le=7)
    tipo_gratificacion:  Optional[str]   = None
    monto_gratificacion: Optional[float] = Field(None, ge=0)
    monto_movilizacion:  Optional[float] = Field(None, ge=0)
    monto_colacion:      Optional[float] = Field(None, ge=0)

    forma_pago:        Optional[str]  = Field(None, pattern=r"^[ECDP]$")
    banco_id:          Optional[int]  = None
    nro_cuenta:        Optional[str]  = Field(None, max_length=30)
    tipo_mov_bancario: Optional[int]  = None

    cargo_id:         Optional[UUID] = None
    sucursal_id:      Optional[UUID] = None
    centro_costo_id:  Optional[UUID] = None
    supervisor_id:    Optional[UUID] = None
    tipo_contrato_id: Optional[UUID] = None
    fecha_contrato:   Optional[date] = None

    regimen_previsional:       Optional[int]   = Field(None, ge=1, le=4)
    afp_id:                    Optional[int]   = None
    cotizacion_voluntaria_afp: Optional[float] = Field(None, ge=0)
    rebaja_imp_cotiz_vol:      Optional[bool]  = None

    regimen_salud:      Optional[str]   = Field(None, pattern=r"^(FONASA|ISAPRE)$")
    isapre_id:          Optional[int]   = None
    modalidad_isapre:   Optional[int]   = Field(None, ge=1, le=6)
    monto_isapre_pesos: Optional[float] = Field(None, ge=0)
    monto_isapre_uf:    Optional[float] = Field(None, ge=0)

    tiene_seg_cesantia:  Optional[bool] = None
    contrato_plazo_fijo: Optional[bool] = None
    fecha_ingreso_sc:    Optional[date] = None
    fecha_ultimo_mes_sc: Optional[date] = None
    afp_seg_cesantia_id: Optional[int]  = None
    no_cotiza_sis:       Optional[bool] = None

    tiene_serv_med_cchc: Optional[bool] = None
    tipo_trabajador:     Optional[int]  = Field(None, ge=1, le=4)
    es_activo:           Optional[bool] = None


class TrabajadorRead(BaseModel):
    id:               UUID
    tenant_id:        UUID
    codigo:           str
    rut:              str
    nombres:          str
    apellido_paterno: str
    apellido_materno: Optional[str]
    nombre_completo:  str
    fecha_nacimiento: Optional[date]
    email:            Optional[str]
    telefono:         Optional[str]
    direccion_calle:  Optional[str]
    direccion_numero: Optional[str]
    region_id:        Optional[int]
    comuna_id:        Optional[int]
    estado_civil:     Optional[int]
    sexo:             Optional[str]
    es_extranjero:    bool
    nacionalidad:     Optional[str]

    tipo_sueldo:         str
    moneda_id:           int
    monto_sueldo:        float
    horas_semana:        Optional[float]
    dias_semana:         Optional[int]
    tipo_gratificacion:  str
    monto_gratificacion: Optional[float]
    monto_movilizacion:  float
    monto_colacion:      float
    forma_pago:          str
    banco_id:            Optional[int]
    nro_cuenta:          Optional[str]
    tipo_mov_bancario:   Optional[int]

    cargo_id:         Optional[UUID]
    sucursal_id:      Optional[UUID]
    centro_costo_id:  Optional[UUID]
    supervisor_id:    Optional[UUID]
    tipo_contrato_id: Optional[UUID]
    fecha_contrato:   Optional[date]

    regimen_previsional:       int
    afp_id:                    Optional[int]
    cotizacion_voluntaria_afp: float
    regimen_salud:             str
    isapre_id:                 Optional[int]
    modalidad_isapre:          Optional[int]
    monto_isapre_pesos:        float
    monto_isapre_uf:           float
    tiene_seg_cesantia:        bool
    contrato_plazo_fijo:       bool
    fecha_ingreso_sc:          Optional[date]
    fecha_ultimo_mes_sc:       Optional[date]
    afp_seg_cesantia_id:       Optional[int]
    no_cotiza_sis:             bool
    tiene_serv_med_cchc:       bool
    tipo_trabajador:           int
    es_activo:                 bool
    created_at:                datetime
    updated_at:                datetime

    model_config = ConfigDict(from_attributes=True)


class TrabajadorListItem(BaseModel):
    """Versión resumida para listados."""
    id:               UUID
    codigo:           str
    rut:              str
    nombre_completo:  str
    cargo_id:         Optional[UUID]
    sucursal_id:      Optional[UUID]
    centro_costo_id:  Optional[UUID]
    es_activo:        bool
    fecha_contrato:   Optional[date]

    model_config = ConfigDict(from_attributes=True)


class TrabajadorList(BaseModel):
    items: list[TrabajadorListItem]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# APV
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorApvCreate(BaseModel):
    tipo_apv:          str   = Field(..., pattern=r"^(normal|colectivo)$")
    moneda_trabajador: str   = Field("CLP", pattern=r"^(CLP|UF|PCT)$")
    monto_trabajador:  float = Field(0, ge=0)
    moneda_empleador:  Optional[str]   = Field(None, pattern=r"^(CLP|UF|PCT)$")
    monto_empleador:   float           = Field(0, ge=0)
    administra_afp:    bool            = True
    afp_id:            Optional[int]   = None
    otra_institucion:  Optional[str]   = Field(None, max_length=100)
    rebaja_art42bis:   bool            = False
    fecha_inicio:      date
    fecha_termino:     Optional[date]  = None


class TrabajadorApvUpdate(BaseModel):
    monto_trabajador: Optional[float] = Field(None, ge=0)
    monto_empleador:  Optional[float] = Field(None, ge=0)
    rebaja_art42bis:  Optional[bool]  = None
    fecha_termino:    Optional[date]  = None
    es_activo:        Optional[bool]  = None


class TrabajadorApvRead(BaseModel):
    id:                UUID
    trabajador_id:     UUID
    tipo_apv:          str
    moneda_trabajador: str
    monto_trabajador:  float
    moneda_empleador:  Optional[str]
    monto_empleador:   float
    administra_afp:    bool
    afp_id:            Optional[int]
    otra_institucion:  Optional[str]
    rebaja_art42bis:   bool
    fecha_inicio:      date
    fecha_termino:     Optional[date]
    es_activo:         bool
    created_at:        datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# CÓNYUGE AFILIADO VOLUNTARIO
# ─────────────────────────────────────────────────────────────────────────────

class ConyugeAfiliadoCreate(BaseModel):
    rut_conyuge:             str   = Field(..., min_length=9, max_length=12)
    nombres:                 str   = Field(..., min_length=2, max_length=200)
    afp_id:                  Optional[int]  = None
    monto_cotiz_voluntaria:  float = Field(0, ge=0)
    monto_deposito_ahorro:   float = Field(0, ge=0)
    fecha_inicio:            date
    fecha_termino:           Optional[date] = None

    @field_validator("rut_conyuge")
    @classmethod
    def validar_rut(cls, v):
        return _validate_rut(v)


class ConyugeAfiliadoUpdate(BaseModel):
    monto_cotiz_voluntaria: Optional[float] = Field(None, ge=0)
    monto_deposito_ahorro:  Optional[float] = Field(None, ge=0)
    fecha_termino:          Optional[date]  = None
    cesar_cotizacion:       Optional[bool]  = None


class ConyugeAfiliadoRead(BaseModel):
    id:                     UUID
    trabajador_id:          UUID
    rut_conyuge:            str
    nombres:                str
    afp_id:                 Optional[int]
    monto_cotiz_voluntaria: float
    monto_deposito_ahorro:  float
    fecha_inicio:           date
    fecha_termino:          Optional[date]
    cesar_cotizacion:       bool
    created_at:             datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# CARGAS FAMILIARES
# ─────────────────────────────────────────────────────────────────────────────

class CargaFamiliarCreate(BaseModel):
    rut:               str  = Field(..., min_length=9, max_length=12)
    nombres:           str  = Field(..., min_length=2, max_length=200)
    fecha_nacimiento:  date
    fecha_vencimiento: date
    tipo_carga:        str  = Field(..., pattern=r"^(simple|maternal|invalidez)$")
    parentesco:        str  = Field(..., pattern=r"^(hijo|conyuge|progenitor|hermano)$")

    @field_validator("rut")
    @classmethod
    def validar_rut(cls, v):
        return _validate_rut(v)

    @model_validator(mode="after")
    def fechas_validas(self):
        if self.fecha_vencimiento <= self.fecha_nacimiento:
            raise ValueError("fecha_vencimiento debe ser posterior a fecha_nacimiento")
        return self


class CargaFamiliarUpdate(BaseModel):
    fecha_vencimiento: Optional[date] = None
    es_activa:         Optional[bool] = None


class CargaFamiliarRead(BaseModel):
    id:                UUID
    trabajador_id:     UUID
    rut:               str
    nombres:           str
    fecha_nacimiento:  date
    fecha_vencimiento: date
    tipo_carga:        str
    parentesco:        str
    es_activa:         bool
    created_at:        datetime

    model_config = ConfigDict(from_attributes=True)


class CargaFamiliarList(BaseModel):
    items: list[CargaFamiliarRead]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# FICHA VACACIONES
# ─────────────────────────────────────────────────────────────────────────────

class FichaVacacionCreate(BaseModel):
    fecha_evento:    date
    descripcion:     Optional[str]  = Field(None, max_length=200)
    fecha_desde:     date
    fecha_hasta:     date
    dias_otorgados:  float          = Field(0, ge=0)
    dias_utilizados: float          = Field(0, ge=0)
    es_progresiva:   bool           = False

    @model_validator(mode="after")
    def fechas_validas(self):
        if self.fecha_hasta < self.fecha_desde:
            raise ValueError("fecha_hasta debe ser igual o posterior a fecha_desde")
        return self


class FichaVacacionUpdate(BaseModel):
    descripcion:     Optional[str]   = Field(None, max_length=200)
    dias_otorgados:  Optional[float] = Field(None, ge=0)
    dias_utilizados: Optional[float] = Field(None, ge=0)


class FichaVacacionRead(BaseModel):
    id:              UUID
    trabajador_id:   UUID
    fecha_evento:    date
    descripcion:     Optional[str]
    fecha_desde:     date
    fecha_hasta:     date
    dias_otorgados:  float
    dias_utilizados: float
    es_progresiva:   bool
    created_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class FichaVacacionList(BaseModel):
    items: list[FichaVacacionRead]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# FICHA PERMISOS
# ─────────────────────────────────────────────────────────────────────────────

class FichaPermisoCreate(BaseModel):
    fecha_evento:    date
    tipo_permiso_id: UUID
    fecha_desde:     date
    fecha_hasta:     date
    dias_otorgados:  float = Field(0, ge=0)
    observaciones:   Optional[str] = None

    @model_validator(mode="after")
    def fechas_validas(self):
        if self.fecha_hasta < self.fecha_desde:
            raise ValueError("fecha_hasta debe ser igual o posterior a fecha_desde")
        return self


class FichaPermisoUpdate(BaseModel):
    dias_otorgados: Optional[float] = Field(None, ge=0)
    observaciones:  Optional[str]   = None


class FichaPermisoRead(BaseModel):
    id:              UUID
    trabajador_id:   UUID
    fecha_evento:    date
    tipo_permiso_id: UUID
    fecha_desde:     date
    fecha_hasta:     date
    dias_otorgados:  float
    observaciones:   Optional[str]
    created_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class FichaPermisoList(BaseModel):
    items: list[FichaPermisoRead]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# OBSERVACIONES
# ─────────────────────────────────────────────────────────────────────────────

class ObservacionCreate(BaseModel):
    fecha_evento:  date
    supervisor_id: Optional[UUID] = None
    tipo:          Optional[str]  = Field(None, max_length=50)
    descripcion:   str            = Field(..., min_length=1)


class ObservacionUpdate(BaseModel):
    tipo:        Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None


class ObservacionRead(BaseModel):
    id:            UUID
    trabajador_id: UUID
    fecha_evento:  date
    supervisor_id: Optional[UUID]
    tipo:          Optional[str]
    descripcion:   str
    created_at:    datetime

    model_config = ConfigDict(from_attributes=True)


class ObservacionList(BaseModel):
    items: list[ObservacionRead]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# CARGOS DESEMPEÑADOS
# ─────────────────────────────────────────────────────────────────────────────

class CargoDesempenadoCreate(BaseModel):
    cargo_id:          Optional[UUID] = None
    cargo_descripcion: Optional[str]  = Field(None, max_length=100)
    fecha_desde:       date
    fecha_hasta:       Optional[date] = None
    observaciones:     Optional[str]  = None

    @model_validator(mode="after")
    def al_menos_un_cargo(self):
        if not self.cargo_id and not self.cargo_descripcion:
            raise ValueError("Debe indicar cargo_id o cargo_descripcion")
        return self


class CargoDesempenadoUpdate(BaseModel):
    fecha_hasta:   Optional[date] = None
    observaciones: Optional[str]  = None


class CargoDesempenadoRead(BaseModel):
    id:                UUID
    trabajador_id:     UUID
    cargo_id:          Optional[UUID]
    cargo_descripcion: Optional[str]
    fecha_desde:       date
    fecha_hasta:       Optional[date]
    observaciones:     Optional[str]
    created_at:        datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIONES DEL TRABAJADOR
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorEvalCuantitativaCreate(BaseModel):
    fecha_evaluacion: date
    evaluacion_id:    UUID
    atributo_id:      UUID
    valor:            float = Field(..., ge=0)
    observaciones:    Optional[str] = None


class TrabajadorEvalCuantitativaRead(BaseModel):
    id:               UUID
    trabajador_id:    UUID
    fecha_evaluacion: date
    evaluacion_id:    UUID
    atributo_id:      UUID
    valor:            float
    observaciones:    Optional[str]
    creado_por_id:    Optional[UUID]
    created_at:       datetime

    model_config = ConfigDict(from_attributes=True)


class TrabajadorEvalCualitativaCreate(BaseModel):
    fecha_evaluacion: date
    evaluacion_id:    UUID
    atributo_id:      UUID
    descripcion:      Optional[str] = None


class TrabajadorEvalCualitativaRead(BaseModel):
    id:               UUID
    trabajador_id:    UUID
    fecha_evaluacion: date
    evaluacion_id:    UUID
    atributo_id:      UUID
    descripcion:      Optional[str]
    creado_por_id:    Optional[UUID]
    created_at:       datetime

    model_config = ConfigDict(from_attributes=True)
