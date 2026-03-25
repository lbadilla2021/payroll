"""
modulos/nomina/calculo/endpoints_calculo.py
============================================
Rutas FastAPI para el motor de cálculo de liquidaciones.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.models.models import User

from modulos.nomina.calculo.schemas_calculo import (
    CalculoEmpresaRequest, CalculoEmpresaResponse,
    ResultadoCalculoSchema,
)
from modulos.nomina.calculo.servicio_calculo import ServicioCalculo
from modulos.nomina.calculo.motor import ResultadoCalculo


def _tenant_id(actor: User) -> UUID:
    return actor.tenant_id


def _resultado_a_schema(r: ResultadoCalculo) -> ResultadoCalculoSchema:
    """Convierte ResultadoCalculo (dataclass) a schema Pydantic."""
    return ResultadoCalculoSchema(
        sueldo_base_proporcional = r.sueldo_base_proporcional,
        valor_hora_extra          = r.valor_hora_extra,
        hh_extra_normales_monto   = r.hh_extra_normales_monto,
        hh_extra_nocturnas_monto  = r.hh_extra_nocturnas_monto,
        hh_extra_festivas_monto   = r.hh_extra_festivas_monto,
        total_horas_extra         = r.total_horas_extra,
        movilizacion              = r.movilizacion,
        colacion                  = r.colacion,
        gratificacion             = r.gratificacion,
        haberes_imponibles        = r.haberes_imponibles,
        haberes_no_imponibles     = r.haberes_no_imponibles,
        total_haberes             = r.total_haberes,
        total_imponible           = r.total_imponible,
        total_tributable          = r.total_tributable,
        descuento_afp             = r.descuento_afp,
        descuento_sis             = r.descuento_sis,
        descuento_salud           = r.descuento_salud,
        diferencia_isapre         = r.diferencia_isapre,
        descuento_seg_cesantia_t  = r.descuento_seg_cesantia_t,
        descuento_seg_cesantia_e  = r.descuento_seg_cesantia_e,
        cotiz_voluntaria_afp      = r.cotiz_voluntaria_afp,
        apv_monto                 = r.apv_monto,
        rebaja_zona_extrema       = r.rebaja_zona_extrema,
        base_impuesto_unico       = r.base_impuesto_unico,
        impuesto_unico            = r.impuesto_unico,
        asignacion_familiar       = r.asignacion_familiar,
        descuentos_varios         = r.descuentos_varios,
        descuentos_prestamos      = r.descuentos_prestamos,
        total_descuentos          = r.total_descuentos,
        anticipo                  = r.anticipo,
        liquido_a_pagar           = r.liquido_a_pagar,
        aporte_acc_trabajo        = r.aporte_acc_trabajo,
    )


router = APIRouter(prefix="/nomina/calculo", tags=["Nómina - Motor de Cálculo"])


@router.post("/movimiento/{movimiento_id}", response_model=ResultadoCalculoSchema)
def calcular_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.calculo.ejecutar")),
):
    """
    Calcula la liquidación de un movimiento mensual individual.
    Persiste los resultados y retorna el desglose completo.
    """
    resultado = ServicioCalculo.calcular_movimiento(db, _tenant_id(actor), movimiento_id)
    return _resultado_a_schema(resultado)


@router.post("/empresa", response_model=CalculoEmpresaResponse)
def calcular_empresa(
    body: CalculoEmpresaRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.calculo.ejecutar")),
):
    """
    Calcula todos los movimientos pendientes del período para la empresa.
    Equivale al 'Cálculo por Empresa' del manual Transtecnia (cap. 5.3).
    """
    resultado = ServicioCalculo.calcular_empresa(
        db, _tenant_id(actor), body.anio, body.mes
    )
    return CalculoEmpresaResponse(**resultado)


@router.get("/movimiento/{movimiento_id}/preview", response_model=ResultadoCalculoSchema)
def preview_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.calculo.ejecutar")),
):
    """
    Calcula SIN persistir — útil para previsualizar antes de confirmar.
    """
    from modulos.nomina.models import MovimientoMensual
    from sqlalchemy import text

    db.execute(text("SET LOCAL app.current_tenant_id = :tid"),
               {"tid": str(_tenant_id(actor))})

    # Verificar que existe
    mov = db.query(MovimientoMensual).filter(
        MovimientoMensual.tenant_id == _tenant_id(actor),
        MovimientoMensual.id == movimiento_id
    ).first()
    if not mov:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")

    # Calcular sin hacer commit
    resultado = ServicioCalculo.calcular_movimiento(db, _tenant_id(actor), movimiento_id)
    db.rollback()  # No persistir

    return _resultado_a_schema(resultado)
