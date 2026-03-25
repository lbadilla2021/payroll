"""
modulos/nomina/schemas_operacional.py
======================================
Schemas Pydantic v2 — Iteración 3.
Entidades operacionales del proceso de remuneraciones:
  - Contrato (+ cláusulas)
  - MovimientoMensual (+ conceptos)
  - Finiquito (+ conceptos)
  - Préstamo (+ cuotas)
  - Anticipo
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATO
# ─────────────────────────────────────────────────────────────────────────────

class ContratoCreate(BaseModel):
    trabajador_id:      UUID
    nro_contrato:       Optional[str]  = Field(None, max_length=20)
    tipo_contrato_id:   Optional[UUID] = None
    fecha_inicio:       date
    fecha_termino:      Optional[date] = None
    cargo_id:           Optional[UUID] = None
    sucursal_id:        Optional[UUID] = None
    centro_costo_id:    Optional[UUID] = None
    labor:              Optional[str]  = Field(None, max_length=200)
    establecimiento:    Optional[str]  = Field(None, max_length=200)
    horario_beneficios: Optional[str]  = Field(None, max_length=100)
    fecha_emision:      Optional[date] = None
    observaciones:      Optional[str]  = None
    clausula_ids:       list[UUID]     = Field(default_factory=list)

    @model_validator(mode="after")
    def fecha_termino_posterior(self):
        if self.fecha_termino and self.fecha_termino <= self.fecha_inicio:
            raise ValueError("fecha_termino debe ser posterior a fecha_inicio")
        return self


class ContratoUpdate(BaseModel):
    tipo_contrato_id:   Optional[UUID] = None
    fecha_termino:      Optional[date] = None
    cargo_id:           Optional[UUID] = None
    sucursal_id:        Optional[UUID] = None
    centro_costo_id:    Optional[UUID] = None
    labor:              Optional[str]  = Field(None, max_length=200)
    establecimiento:    Optional[str]  = Field(None, max_length=200)
    horario_beneficios: Optional[str]  = Field(None, max_length=100)
    fecha_emision:      Optional[date] = None
    observaciones:      Optional[str]  = None
    estado:             Optional[str]  = Field(None, pattern=r"^(vigente|finiquitado|vencido)$")
    clausula_ids:       Optional[list[UUID]] = None


class ContratoRead(BaseModel):
    id:                 UUID
    tenant_id:          UUID
    trabajador_id:      UUID
    nro_contrato:       Optional[str]
    tipo_contrato_id:   Optional[UUID]
    fecha_inicio:       date
    fecha_termino:      Optional[date]
    cargo_id:           Optional[UUID]
    sucursal_id:        Optional[UUID]
    centro_costo_id:    Optional[UUID]
    labor:              Optional[str]
    establecimiento:    Optional[str]
    horario_beneficios: Optional[str]
    fecha_emision:      Optional[date]
    observaciones:      Optional[str]
    estado:             str
    created_at:         datetime
    updated_at:         datetime

    model_config = ConfigDict(from_attributes=True)


class ContratoListItem(BaseModel):
    id:             UUID
    trabajador_id:  UUID
    nro_contrato:   Optional[str]
    fecha_inicio:   date
    fecha_termino:  Optional[date]
    cargo_id:       Optional[UUID]
    sucursal_id:    Optional[UUID]
    estado:         str
    created_at:     datetime

    model_config = ConfigDict(from_attributes=True)


class ContratoList(BaseModel):
    items: list[ContratoListItem]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO MENSUAL
# ─────────────────────────────────────────────────────────────────────────────

class MovimientoMensualCreate(BaseModel):
    trabajador_id:      UUID
    anio:               int   = Field(..., ge=2020, le=2100)
    mes:                int   = Field(..., ge=1, le=12)
    nro_movimiento:     int   = Field(1, ge=1, le=9)

    # Situación del mes (cap. 5.2.1)
    dias_ausentes:      Decimal = Field(Decimal("0"), ge=0)
    dias_no_contratado: Decimal = Field(Decimal("0"), ge=0)
    dias_licencia:      Decimal = Field(Decimal("0"), ge=0)
    dias_movilizacion:  Decimal = Field(Decimal("0"), ge=0)
    dias_colacion:      Decimal = Field(Decimal("0"), ge=0)
    dias_vacaciones:    Decimal = Field(Decimal("0"), ge=0)

    # Rentas otro empleador
    otras_rentas:       Decimal = Field(Decimal("0"), ge=0)
    monto_isapre_otro:  Decimal = Field(Decimal("0"), ge=0)
    monto_salud_iu:     Decimal = Field(Decimal("0"), ge=0)

    # Horas extras
    hh_extras_normales:  Decimal = Field(Decimal("0"), ge=0)
    hh_extras_nocturnas: Decimal = Field(Decimal("0"), ge=0)
    hh_extras_festivas:  Decimal = Field(Decimal("0"), ge=0)

    # Cargas retroactivas
    cargas_retroactivas:     int = Field(0, ge=0)
    cargas_retro_simples:    int = Field(0, ge=0)
    cargas_retro_invalidez:  int = Field(0, ge=0)
    cargas_retro_maternales: int = Field(0, ge=0)

    # Movimiento (cap. 5.2.4)
    codigo_movimiento:      int  = Field(0, ge=0, le=11)
    fecha_inicio_mov:       Optional[date] = None
    fecha_termino_mov:      Optional[date] = None
    fecha_inicio_licencia:  Optional[date] = None
    fecha_termino_licencia: Optional[date] = None
    rut_entidad_pagadora:   Optional[str]  = Field(None, max_length=12)

    imponible_sc_mes_anterior:   Decimal = Field(Decimal("0"), ge=0)
    imponible_prev_mes_anterior: Decimal = Field(Decimal("0"), ge=0)

    anticipo: Decimal = Field(Decimal("0"), ge=0)


class MovimientoMensualUpdate(BaseModel):
    """Solo campos editables antes de calcular."""
    dias_ausentes:           Optional[Decimal] = Field(None, ge=0)
    dias_no_contratado:      Optional[Decimal] = Field(None, ge=0)
    dias_licencia:           Optional[Decimal] = Field(None, ge=0)
    dias_movilizacion:       Optional[Decimal] = Field(None, ge=0)
    dias_colacion:           Optional[Decimal] = Field(None, ge=0)
    dias_vacaciones:         Optional[Decimal] = Field(None, ge=0)
    otras_rentas:            Optional[Decimal] = Field(None, ge=0)
    monto_isapre_otro:       Optional[Decimal] = Field(None, ge=0)
    monto_salud_iu:          Optional[Decimal] = Field(None, ge=0)
    hh_extras_normales:      Optional[Decimal] = Field(None, ge=0)
    hh_extras_nocturnas:     Optional[Decimal] = Field(None, ge=0)
    hh_extras_festivas:      Optional[Decimal] = Field(None, ge=0)
    cargas_retroactivas:     Optional[int]     = Field(None, ge=0)
    cargas_retro_simples:    Optional[int]     = Field(None, ge=0)
    cargas_retro_invalidez:  Optional[int]     = Field(None, ge=0)
    cargas_retro_maternales: Optional[int]     = Field(None, ge=0)
    codigo_movimiento:       Optional[int]     = Field(None, ge=0, le=11)
    fecha_inicio_mov:        Optional[date]    = None
    fecha_termino_mov:       Optional[date]    = None
    fecha_inicio_licencia:   Optional[date]    = None
    fecha_termino_licencia:  Optional[date]    = None
    rut_entidad_pagadora:    Optional[str]     = Field(None, max_length=12)
    imponible_sc_mes_anterior:   Optional[Decimal] = Field(None, ge=0)
    imponible_prev_mes_anterior: Optional[Decimal] = Field(None, ge=0)
    anticipo:                Optional[Decimal] = Field(None, ge=0)


class MovimientoMensualRead(BaseModel):
    id:                          UUID
    tenant_id:                   UUID
    trabajador_id:               UUID
    anio:                        int
    mes:                         int
    nro_movimiento:              int

    dias_ausentes:               Decimal
    dias_no_contratado:          Decimal
    dias_licencia:               Decimal
    dias_movilizacion:           Decimal
    dias_colacion:               Decimal
    dias_vacaciones:             Decimal

    otras_rentas:                Decimal
    monto_isapre_otro:           Decimal
    monto_salud_iu:              Decimal

    hh_extras_normales:          Decimal
    hh_extras_nocturnas:         Decimal
    hh_extras_festivas:          Decimal

    cargas_retroactivas:         int
    cargas_retro_simples:        int
    cargas_retro_invalidez:      int
    cargas_retro_maternales:     int

    codigo_movimiento:           int
    fecha_inicio_mov:            Optional[date]
    fecha_termino_mov:           Optional[date]
    fecha_inicio_licencia:       Optional[date]
    fecha_termino_licencia:      Optional[date]
    rut_entidad_pagadora:        Optional[str]

    imponible_sc_mes_anterior:   Decimal
    imponible_prev_mes_anterior: Decimal

    # Resultados calculados
    total_haberes:      Optional[Decimal]
    total_imponible:    Optional[Decimal]
    total_tributable:   Optional[Decimal]
    descuento_afp:      Optional[Decimal]
    descuento_salud:    Optional[Decimal]
    impuesto_unico:     Optional[Decimal]
    total_descuentos:   Optional[Decimal]
    liquido_pagar:      Optional[Decimal]
    anticipo:           Decimal

    estado:             str
    calculado_en:       Optional[datetime]
    created_at:         datetime
    updated_at:         datetime

    model_config = ConfigDict(from_attributes=True)


class MovimientoMensualListItem(BaseModel):
    id:             UUID
    trabajador_id:  UUID
    anio:           int
    mes:            int
    nro_movimiento: int
    estado:         str
    liquido_pagar:  Optional[Decimal]
    calculado_en:   Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class MovimientoMensualList(BaseModel):
    items: list[MovimientoMensualListItem]
    total: int
    page:  int
    size:  int


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO CONCEPTO (haberes/descuentos del movimiento)
# ─────────────────────────────────────────────────────────────────────────────

class MovimientoConceptoCreate(BaseModel):
    concepto_id:      UUID
    tipo:             str     = Field(..., pattern=r"^[HD]$")
    valor:            Decimal = Field(..., ge=0)
    cantidad:         Decimal = Field(Decimal("1"), ge=0)
    ocurrencia:       int     = Field(1, ge=1)
    es_semana_corrida: bool   = False


class MovimientoConceptoUpdate(BaseModel):
    valor:     Optional[Decimal] = Field(None, ge=0)
    cantidad:  Optional[Decimal] = Field(None, ge=0)
    ocurrencia: Optional[int]   = Field(None, ge=1)


class MovimientoConceptoRead(BaseModel):
    id:               UUID
    movimiento_id:    UUID
    concepto_id:      UUID
    tipo:             str
    valor:            Decimal
    cantidad:         Decimal
    ocurrencia:       int
    monto_calculado:  Decimal
    es_semana_corrida: bool
    created_at:       datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# FINIQUITO
# ─────────────────────────────────────────────────────────────────────────────

class FiniquitoCreate(BaseModel):
    trabajador_id:       UUID
    movimiento_id:       Optional[UUID] = None
    contrato_id:         Optional[UUID] = None
    fecha_inicio:        date
    fecha_finiquito:     date
    cargo_id:            Optional[UUID] = None
    causal_id:           Optional[UUID] = None
    descripcion_pago:    Optional[str]  = None
    importa_liquidacion: bool           = False

    @model_validator(mode="after")
    def fechas_validas(self):
        if self.fecha_finiquito < self.fecha_inicio:
            raise ValueError("fecha_finiquito debe ser igual o posterior a fecha_inicio")
        return self


class FiniquitoUpdate(BaseModel):
    causal_id:        Optional[UUID] = None
    descripcion_pago: Optional[str]  = None
    estado:           Optional[str]  = Field(None, pattern=r"^(borrador|firmado|pagado)$")
    total_finiquito:  Optional[Decimal] = Field(None, ge=0)


class FiniquitoRead(BaseModel):
    id:                  UUID
    tenant_id:           UUID
    trabajador_id:       UUID
    movimiento_id:       Optional[UUID]
    contrato_id:         Optional[UUID]
    fecha_inicio:        date
    fecha_finiquito:     date
    cargo_id:            Optional[UUID]
    causal_id:           Optional[UUID]
    descripcion_pago:    Optional[str]
    importa_liquidacion: bool
    total_finiquito:     Optional[Decimal]
    estado:              str
    created_at:          datetime
    updated_at:          datetime

    model_config = ConfigDict(from_attributes=True)


class FiniquitoList(BaseModel):
    items: list[FiniquitoRead]
    total: int
    page:  int
    size:  int


class FiniquitoConceptoCreate(BaseModel):
    descripcion: str     = Field(..., min_length=1, max_length=200)
    monto:       Decimal = Field(..., ge=0)
    es_haber:    bool    = True


class FiniquitoConceptoRead(BaseModel):
    id:          UUID
    finiquito_id: UUID
    descripcion: str
    monto:       Decimal
    es_haber:    bool
    created_at:  datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# PRÉSTAMO
# ─────────────────────────────────────────────────────────────────────────────

class PrestamoCreate(BaseModel):
    trabajador_id: UUID
    concepto_id:   UUID
    monto_total:   Decimal = Field(..., gt=0)
    nro_cuotas:    int     = Field(..., ge=1, le=120)
    fecha_inicio:  date
    valor_cuota:   Optional[Decimal] = Field(None, gt=0)

    @model_validator(mode="after")
    def calcular_cuota(self):
        """Si no se informa valor_cuota, se calcula automáticamente."""
        if self.valor_cuota is None:
            self.valor_cuota = round(self.monto_total / self.nro_cuotas, 0)
        return self


class PrestamoRead(BaseModel):
    id:              UUID
    tenant_id:       UUID
    trabajador_id:   UUID
    concepto_id:     UUID
    monto_total:     Decimal
    nro_cuotas:      int
    valor_cuota:     Decimal
    fecha_inicio:    date
    saldo_pendiente: Decimal
    estado:          str
    created_at:      datetime
    updated_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class PrestamoList(BaseModel):
    items: list[PrestamoRead]
    total: int
    page:  int
    size:  int


class PrestamoCuotaRead(BaseModel):
    id:           UUID
    prestamo_id:  UUID
    nro_cuota:    int
    anio:         int
    mes:          int
    monto:        Decimal
    procesar:     bool
    pagada:       bool
    fecha_pago:   Optional[date]
    movimiento_id: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class PrestamoCuotaUpdate(BaseModel):
    procesar:   Optional[bool] = None
    pagada:     Optional[bool] = None
    fecha_pago: Optional[date] = None


class PagoAnticipadoRequest(BaseModel):
    """Para pago anticipado de cuota(s) de un préstamo."""
    nro_cuotas:         list[int] = Field(..., min_length=1)
    agregar_movimiento: bool      = True
    concepto_id:        Optional[UUID] = None  # si agregar_movimiento=True


# ─────────────────────────────────────────────────────────────────────────────
# ANTICIPO
# ─────────────────────────────────────────────────────────────────────────────

class AnticipoCreate(BaseModel):
    trabajador_id:  UUID
    anio:           int     = Field(..., ge=2020, le=2100)
    mes:            int     = Field(..., ge=1, le=12)
    monto:          Decimal = Field(..., gt=0)
    fecha_emision:  date
    sucursal_id:    Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None


class AnticipoUpdate(BaseModel):
    monto:   Optional[Decimal] = Field(None, gt=0)
    estado:  Optional[str]     = Field(None, pattern=r"^(pendiente|procesado|anulado)$")


class AnticipoRead(BaseModel):
    id:              UUID
    tenant_id:       UUID
    trabajador_id:   UUID
    anio:            int
    mes:             int
    monto:           Decimal
    fecha_emision:   date
    sucursal_id:     Optional[UUID]
    centro_costo_id: Optional[UUID]
    estado:          str
    created_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class AnticipoList(BaseModel):
    items: list[AnticipoRead]
    total: int
    page:  int
    size:  int
