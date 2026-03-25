"""
modulos/nomina/endpoints_operacional.py
========================================
Rutas FastAPI — Iteración 3: entidades operacionales de Nómina.
Contrato, MovimientoMensual, Finiquito, Préstamo, Anticipo.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.models.models import User

from modulos.nomina.schemas_operacional import (
    AnticipoCreate, AnticipoList, AnticipoRead, AnticipoUpdate,
    ContratoCreate, ContratoList, ContratoListItem, ContratoRead, ContratoUpdate,
    FiniquitoConceptoCreate, FiniquitoConceptoRead,
    FiniquitoCreate, FiniquitoList, FiniquitoRead, FiniquitoUpdate,
    MovimientoConceptoCreate, MovimientoConceptoRead, MovimientoConceptoUpdate,
    MovimientoMensualCreate, MovimientoMensualList,
    MovimientoMensualListItem, MovimientoMensualRead, MovimientoMensualUpdate,
    PagoAnticipadoRequest, PrestamoCreate, PrestamoList, PrestamoRead,
    PrestamoCuotaRead, PrestamoCuotaUpdate,
)
from modulos.nomina.services_operacional import (
    AnticipoService, ContratoService, FiniquitoService,
    MovimientoMensualService, PrestamoService,
)


def _tenant_id(actor: User) -> UUID:
    return actor.tenant_id


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATOS
# ─────────────────────────────────────────────────────────────────────────────

router_contrato = APIRouter(prefix="/nomina/contratos", tags=["Nómina - Contratos"])


@router_contrato.get("", response_model=ContratoList)
def list_contratos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    trabajador_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.contratos.read")),
):
    items, total = ContratoService.list(
        db, _tenant_id(actor), page, size, trabajador_id, estado
    )
    return ContratoList(
        items=[ContratoListItem.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_contrato.post("", response_model=ContratoRead, status_code=status.HTTP_201_CREATED)
def create_contrato(
    body: ContratoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.contratos.create")),
):
    return ContratoRead.model_validate(
        ContratoService.create(db, _tenant_id(actor), body)
    )


@router_contrato.get("/{contrato_id}", response_model=ContratoRead)
def get_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.contratos.read")),
):
    return ContratoRead.model_validate(
        ContratoService.get_or_404(db, _tenant_id(actor), contrato_id)
    )


@router_contrato.patch("/{contrato_id}", response_model=ContratoRead)
def update_contrato(
    contrato_id: UUID,
    body: ContratoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.contratos.update")),
):
    return ContratoRead.model_validate(
        ContratoService.update(db, _tenant_id(actor), contrato_id, body)
    )


@router_contrato.patch("/{contrato_id}/finalizar", response_model=ContratoRead)
def finalizar_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.contratos.update")),
):
    """Marca el contrato como finiquitado."""
    return ContratoRead.model_validate(
        ContratoService.finalizar(db, _tenant_id(actor), contrato_id)
    )


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTOS MENSUALES
# ─────────────────────────────────────────────────────────────────────────────

router_movimiento = APIRouter(prefix="/nomina/movimientos", tags=["Nómina - Movimientos Mensuales"])


@router_movimiento.get("", response_model=MovimientoMensualList)
def list_movimientos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    anio: Optional[int] = Query(None),
    mes: Optional[int] = Query(None, ge=1, le=12),
    trabajador_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.read")),
):
    items, total = MovimientoMensualService.list(
        db, _tenant_id(actor), page, size, anio, mes, trabajador_id, estado
    )
    return MovimientoMensualList(
        items=[MovimientoMensualListItem.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_movimiento.post("", response_model=MovimientoMensualRead,
                        status_code=status.HTTP_201_CREATED)
def create_movimiento(
    body: MovimientoMensualCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.create")),
):
    return MovimientoMensualRead.model_validate(
        MovimientoMensualService.create(db, _tenant_id(actor), body)
    )


@router_movimiento.get("/resumen/{anio}/{mes}")
def resumen_periodo(
    anio: int, mes: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.read")),
):
    """Estadísticas del período para el dashboard."""
    return MovimientoMensualService.resumen_periodo(db, _tenant_id(actor), anio, mes)


@router_movimiento.get("/trabajador/{trabajador_id}/{anio}/{mes}",
                       response_model=list[MovimientoMensualRead])
def get_movimientos_trabajador_periodo(
    trabajador_id: UUID, anio: int, mes: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.read")),
):
    items = MovimientoMensualService.get_por_trabajador_periodo(
        db, _tenant_id(actor), trabajador_id, anio, mes
    )
    return [MovimientoMensualRead.model_validate(i) for i in items]


@router_movimiento.get("/{movimiento_id}", response_model=MovimientoMensualRead)
def get_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.read")),
):
    return MovimientoMensualRead.model_validate(
        MovimientoMensualService.get_or_404(db, _tenant_id(actor), movimiento_id)
    )


@router_movimiento.patch("/{movimiento_id}", response_model=MovimientoMensualRead)
def update_movimiento(
    movimiento_id: UUID,
    body: MovimientoMensualUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.update")),
):
    return MovimientoMensualRead.model_validate(
        MovimientoMensualService.update(db, _tenant_id(actor), movimiento_id, body)
    )


@router_movimiento.delete("/{movimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.delete")),
):
    MovimientoMensualService.delete(db, _tenant_id(actor), movimiento_id)


# ── Conceptos del movimiento ──────────────────────────────────────────────────

@router_movimiento.get("/{movimiento_id}/conceptos",
                       response_model=list[MovimientoConceptoRead])
def list_conceptos_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.read")),
):
    return [MovimientoConceptoRead.model_validate(i)
            for i in MovimientoMensualService.list_conceptos(
                db, _tenant_id(actor), movimiento_id
            )]


@router_movimiento.post("/{movimiento_id}/conceptos",
                        response_model=MovimientoConceptoRead,
                        status_code=status.HTTP_201_CREATED)
def add_concepto_movimiento(
    movimiento_id: UUID,
    body: MovimientoConceptoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.update")),
):
    return MovimientoConceptoRead.model_validate(
        MovimientoMensualService.add_concepto(db, _tenant_id(actor), movimiento_id, body)
    )


@router_movimiento.patch("/{movimiento_id}/conceptos/{concepto_mov_id}",
                         response_model=MovimientoConceptoRead)
def update_concepto_movimiento(
    movimiento_id: UUID,
    concepto_mov_id: UUID,
    body: MovimientoConceptoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.update")),
):
    return MovimientoConceptoRead.model_validate(
        MovimientoMensualService.update_concepto(db, _tenant_id(actor), concepto_mov_id, body)
    )


@router_movimiento.delete("/{movimiento_id}/conceptos/{concepto_mov_id}",
                          status_code=status.HTTP_204_NO_CONTENT)
def delete_concepto_movimiento(
    movimiento_id: UUID,
    concepto_mov_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.movimientos.update")),
):
    MovimientoMensualService.delete_concepto(db, _tenant_id(actor), concepto_mov_id)


# ─────────────────────────────────────────────────────────────────────────────
# FINIQUITOS
# ─────────────────────────────────────────────────────────────────────────────

router_finiquito = APIRouter(prefix="/nomina/finiquitos", tags=["Nómina - Finiquitos"])


@router_finiquito.get("", response_model=FiniquitoList)
def list_finiquitos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    trabajador_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.read")),
):
    items, total = FiniquitoService.list(
        db, _tenant_id(actor), page, size, trabajador_id, estado, anio
    )
    return FiniquitoList(
        items=[FiniquitoRead.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_finiquito.post("", response_model=FiniquitoRead,
                       status_code=status.HTTP_201_CREATED)
def create_finiquito(
    body: FiniquitoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.create")),
):
    return FiniquitoRead.model_validate(
        FiniquitoService.create(db, _tenant_id(actor), body)
    )


@router_finiquito.get("/{finiquito_id}", response_model=FiniquitoRead)
def get_finiquito(
    finiquito_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.read")),
):
    return FiniquitoRead.model_validate(
        FiniquitoService.get_or_404(db, _tenant_id(actor), finiquito_id)
    )


@router_finiquito.patch("/{finiquito_id}", response_model=FiniquitoRead)
def update_finiquito(
    finiquito_id: UUID,
    body: FiniquitoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.update")),
):
    return FiniquitoRead.model_validate(
        FiniquitoService.update(db, _tenant_id(actor), finiquito_id, body)
    )


# ── Conceptos del finiquito ───────────────────────────────────────────────────

@router_finiquito.get("/{finiquito_id}/conceptos",
                      response_model=list[FiniquitoConceptoRead])
def list_conceptos_finiquito(
    finiquito_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.read")),
):
    return [FiniquitoConceptoRead.model_validate(i)
            for i in FiniquitoService.list_conceptos(db, _tenant_id(actor), finiquito_id)]


@router_finiquito.post("/{finiquito_id}/conceptos",
                       response_model=FiniquitoConceptoRead,
                       status_code=status.HTTP_201_CREATED)
def add_concepto_finiquito(
    finiquito_id: UUID,
    body: FiniquitoConceptoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.update")),
):
    return FiniquitoConceptoRead.model_validate(
        FiniquitoService.add_concepto(db, _tenant_id(actor), finiquito_id, body)
    )


@router_finiquito.delete("/{finiquito_id}/conceptos/{concepto_id}",
                         status_code=status.HTTP_204_NO_CONTENT)
def delete_concepto_finiquito(
    finiquito_id: UUID,
    concepto_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.finiquitos.update")),
):
    FiniquitoService.delete_concepto(db, _tenant_id(actor), finiquito_id, concepto_id)


# ─────────────────────────────────────────────────────────────────────────────
# PRÉSTAMOS
# ─────────────────────────────────────────────────────────────────────────────

router_prestamo = APIRouter(prefix="/nomina/prestamos", tags=["Nómina - Préstamos"])


@router_prestamo.get("", response_model=PrestamoList)
def list_prestamos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    trabajador_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.read")),
):
    items, total = PrestamoService.list(
        db, _tenant_id(actor), page, size, trabajador_id, estado
    )
    return PrestamoList(
        items=[PrestamoRead.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_prestamo.post("", response_model=PrestamoRead,
                      status_code=status.HTTP_201_CREATED)
def create_prestamo(
    body: PrestamoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.create")),
):
    """Crea el préstamo y genera automáticamente todas las cuotas."""
    return PrestamoRead.model_validate(
        PrestamoService.create(db, _tenant_id(actor), body)
    )


@router_prestamo.get("/{prestamo_id}", response_model=PrestamoRead)
def get_prestamo(
    prestamo_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.read")),
):
    return PrestamoRead.model_validate(
        PrestamoService.get_or_404(db, _tenant_id(actor), prestamo_id)
    )


@router_prestamo.get("/{prestamo_id}/cuotas", response_model=list[PrestamoCuotaRead])
def get_cuotas_prestamo(
    prestamo_id: UUID,
    solo_pendientes: bool = Query(False),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.read")),
):
    return [PrestamoCuotaRead.model_validate(i)
            for i in PrestamoService.get_cuotas(
                db, _tenant_id(actor), prestamo_id, solo_pendientes
            )]


@router_prestamo.patch("/{prestamo_id}/cuotas/{cuota_id}",
                       response_model=PrestamoCuotaRead)
def update_cuota_prestamo(
    prestamo_id: UUID,
    cuota_id: UUID,
    body: PrestamoCuotaUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.update")),
):
    return PrestamoCuotaRead.model_validate(
        PrestamoService.update_cuota(db, _tenant_id(actor), cuota_id, body)
    )


@router_prestamo.post("/{prestamo_id}/pago-anticipado")
def pago_anticipado_prestamo(
    prestamo_id: UUID,
    body: PagoAnticipadoRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.update")),
):
    """Marca cuotas seleccionadas como pagadas anticipadamente."""
    return PrestamoService.pago_anticipado(db, _tenant_id(actor), prestamo_id, body)


@router_prestamo.patch("/{prestamo_id}/cancelar", response_model=PrestamoRead)
def cancelar_prestamo(
    prestamo_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.prestamos.delete")),
):
    return PrestamoRead.model_validate(
        PrestamoService.cancelar(db, _tenant_id(actor), prestamo_id)
    )


# ─────────────────────────────────────────────────────────────────────────────
# ANTICIPOS
# ─────────────────────────────────────────────────────────────────────────────

router_anticipo = APIRouter(prefix="/nomina/anticipos", tags=["Nómina - Anticipos"])


@router_anticipo.get("", response_model=AnticipoList)
def list_anticipos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    trabajador_id: Optional[UUID] = Query(None),
    anio: Optional[int] = Query(None),
    mes: Optional[int] = Query(None, ge=1, le=12),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.anticipos.read")),
):
    items, total = AnticipoService.list(
        db, _tenant_id(actor), page, size, trabajador_id, anio, mes, estado
    )
    return AnticipoList(
        items=[AnticipoRead.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_anticipo.post("", response_model=AnticipoRead,
                      status_code=status.HTTP_201_CREATED)
def create_anticipo(
    body: AnticipoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.anticipos.create")),
):
    return AnticipoRead.model_validate(
        AnticipoService.create(db, _tenant_id(actor), body)
    )


@router_anticipo.get("/resumen/{trabajador_id}/{anio}/{mes}")
def resumen_anticipos_trabajador(
    trabajador_id: UUID, anio: int, mes: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.anticipos.read")),
):
    return AnticipoService.resumen_periodo(
        db, _tenant_id(actor), trabajador_id, anio, mes
    )


@router_anticipo.get("/{anticipo_id}", response_model=AnticipoRead)
def get_anticipo(
    anticipo_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.anticipos.read")),
):
    return AnticipoRead.model_validate(
        AnticipoService.get_or_404(db, _tenant_id(actor), anticipo_id)
    )


@router_anticipo.patch("/{anticipo_id}", response_model=AnticipoRead)
def update_anticipo(
    anticipo_id: UUID,
    body: AnticipoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.anticipos.update")),
):
    return AnticipoRead.model_validate(
        AnticipoService.update(db, _tenant_id(actor), anticipo_id, body)
    )


@router_anticipo.patch("/{anticipo_id}/anular", response_model=AnticipoRead)
def anular_anticipo(
    anticipo_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.anticipos.delete")),
):
    return AnticipoRead.model_validate(
        AnticipoService.anular(db, _tenant_id(actor), anticipo_id)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Router operacional (se agrega al router principal de nomina)
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()
router.include_router(router_contrato)
router.include_router(router_movimiento)
router.include_router(router_finiquito)
router.include_router(router_prestamo)
router.include_router(router_anticipo)
