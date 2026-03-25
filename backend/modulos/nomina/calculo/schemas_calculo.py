"""
modulos/nomina/calculo/schemas_calculo.py
==========================================
Schemas Pydantic para el motor de cálculo y liquidaciones.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResultadoCalculoSchema(BaseModel):
    """Resultado completo del cálculo de liquidación."""

    # Haberes
    sueldo_base_proporcional: Decimal
    valor_hora_extra:          Decimal
    hh_extra_normales_monto:   Decimal
    hh_extra_nocturnas_monto:  Decimal
    hh_extra_festivas_monto:   Decimal
    total_horas_extra:         Decimal
    movilizacion:              Decimal
    colacion:                  Decimal
    gratificacion:             Decimal
    haberes_imponibles:        Decimal
    haberes_no_imponibles:     Decimal
    total_haberes:             Decimal

    # Bases
    total_imponible:           Decimal
    total_tributable:          Decimal

    # Cotizaciones previsionales
    descuento_afp:             Decimal
    descuento_sis:             Decimal
    descuento_salud:           Decimal
    diferencia_isapre:         Decimal
    descuento_seg_cesantia_t:  Decimal
    descuento_seg_cesantia_e:  Decimal
    cotiz_voluntaria_afp:      Decimal
    apv_monto:                 Decimal

    # Impuesto
    rebaja_zona_extrema:       Decimal
    base_impuesto_unico:       Decimal
    impuesto_unico:            Decimal

    # Cargas familiares
    asignacion_familiar:       Decimal

    # Descuentos
    descuentos_varios:         Decimal
    descuentos_prestamos:      Decimal
    total_descuentos:          Decimal

    # Resultado
    anticipo:                  Decimal
    liquido_a_pagar:           Decimal

    # Empleador (informativo)
    aporte_acc_trabajo:        Decimal


class CalculoRequest(BaseModel):
    """Request para calcular un movimiento individual."""
    movimiento_id: UUID


class CalculoEmpresaRequest(BaseModel):
    """Request para calcular todos los movimientos del período."""
    anio: int
    mes:  int


class CalculoEmpresaResponse(BaseModel):
    """Respuesta del cálculo masivo."""
    anio:              int
    mes:               int
    total_movimientos: int
    procesados:        int
    errores:           int
    detalle_errores:   list[dict]


class LiquidacionDetalleSchema(BaseModel):
    """
    Liquidación completa de un trabajador: datos del movimiento + resultado del cálculo.
    Se usa para imprimir la liquidación de sueldo.
    """
    # Identificación
    movimiento_id:      UUID
    trabajador_id:      UUID
    rut:                str
    nombre_completo:    str
    anio:               int
    mes:                int
    nro_movimiento:     int

    # Datos laborales del período
    cargo:              Optional[str]
    sucursal:           Optional[str]
    centro_costo:       Optional[str]
    afp:                Optional[str]
    isapre_fonasa:      Optional[str]
    dias_trabajados:    Decimal
    dias_ausentes:      Decimal
    dias_licencia:      Decimal

    # Resultado del cálculo
    calculo:            ResultadoCalculoSchema

    model_config = ConfigDict(from_attributes=True)
