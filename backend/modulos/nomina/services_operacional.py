"""
modulos/nomina/services_operacional.py
======================================
Servicios para entidades operacionales de Nómina — Iteración 3.
Reglas de negocio chilenas aplicadas:
  - Contrato: no se puede crear un 2do vigente sin finiquitar el anterior.
  - Movimiento: bloqueado si el período está cerrado.
  - Finiquito: solo se puede firmar si tiene causal y al menos un concepto.
  - Préstamo: las cuotas se generan automáticamente al crear.
  - Anticipo: se valida que el período no esté cerrado.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from modulos.nomina.repositories import ParametroMensualRepository
from modulos.nomina.repositories_operacional import (
    AnticipoRepository, ContratoRepository,
    FiniquitoRepository, MovimientoMensualRepository, PrestamoRepository,
)
from modulos.nomina.schemas_operacional import (
    AnticipoCreate, AnticipoUpdate,
    ContratoCreate, ContratoUpdate,
    FiniquitoConceptoCreate, FiniquitoCreate, FiniquitoUpdate,
    MovimientoConceptoCreate, MovimientoConceptoUpdate,
    MovimientoMensualCreate, MovimientoMensualUpdate,
    PagoAnticipadoRequest, PrestamoCreate,
    PrestamoCuotaUpdate,
)


def _verificar_periodo_no_bloqueado(db: Session, tenant_id: UUID,
                                     anio: int, mes: int) -> None:
    """Lanza excepción si el período está bloqueado o cerrado."""
    params = ParametroMensualRepository.get_by_periodo(db, tenant_id, anio, mes)
    if params and params.bloqueado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El período {anio}/{mes:02d} está bloqueado."
        )
    if params and params.cerrado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El período {anio}/{mes:02d} ya fue cerrado."
        )


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATO
# ─────────────────────────────────────────────────────────────────────────────

class ContratoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             trabajador_id: Optional[UUID], estado: Optional[str]):
        return ContratoRepository.get_all(
            db, tenant_id, page, size, trabajador_id, estado
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, contrato_id: UUID):
        obj = ContratoRepository.get_by_id(db, tenant_id, contrato_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Contrato no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: ContratoCreate):
        # Validar que no haya otro contrato vigente para el mismo trabajador
        vigente = ContratoRepository.get_vigente_trabajador(
            db, tenant_id, body.trabajador_id
        )
        if vigente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El trabajador ya tiene un contrato vigente (ID: {vigente.id}). "
                       "Finalícelo antes de crear uno nuevo."
            )
        data = body.model_dump()
        obj = ContratoRepository.create(db, tenant_id, data)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, contrato_id: UUID, body: ContratoUpdate):
        obj = ContratoService.get_or_404(db, tenant_id, contrato_id)
        if obj.estado == "finiquitado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede modificar un contrato finiquitado."
            )
        data = body.model_dump(exclude_unset=True)
        updated = ContratoRepository.update(db, tenant_id, obj, data)
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def finalizar(db: Session, tenant_id: UUID, contrato_id: UUID):
        """Marca el contrato como finiquitado."""
        obj = ContratoService.get_or_404(db, tenant_id, contrato_id)
        if obj.estado != "vigente":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se puede finalizar un contrato vigente. Estado actual: {obj.estado}"
            )
        obj.estado = "finiquitado"
        db.commit()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO MENSUAL
# ─────────────────────────────────────────────────────────────────────────────

class MovimientoMensualService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             anio: Optional[int], mes: Optional[int],
             trabajador_id: Optional[UUID], estado: Optional[str]):
        return MovimientoMensualRepository.get_all(
            db, tenant_id, page, size, anio, mes, trabajador_id, estado
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, movimiento_id: UUID):
        obj = MovimientoMensualRepository.get_by_id(db, tenant_id, movimiento_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Movimiento mensual no encontrado.")
        return obj

    @staticmethod
    def get_por_trabajador_periodo(db: Session, tenant_id: UUID,
                                   trabajador_id: UUID, anio: int, mes: int):
        return MovimientoMensualRepository.get_by_periodo_trabajador(
            db, tenant_id, trabajador_id, anio, mes
        )

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: MovimientoMensualCreate):
        _verificar_periodo_no_bloqueado(db, tenant_id, body.anio, body.mes)

        # Validar que no exista ya este nro_movimiento para el trabajador/período
        existentes = MovimientoMensualRepository.get_by_periodo_trabajador(
            db, tenant_id, body.trabajador_id, body.anio, body.mes
        )
        nums_existentes = [m.nro_movimiento for m in existentes]
        if body.nro_movimiento in nums_existentes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe movimiento {body.nro_movimiento} para este trabajador "
                       f"en {body.anio}/{body.mes:02d}."
            )

        obj = MovimientoMensualRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, movimiento_id: UUID,
               body: MovimientoMensualUpdate):
        obj = MovimientoMensualService.get_or_404(db, tenant_id, movimiento_id)
        if obj.estado == "cerrado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede modificar un movimiento cerrado."
            )
        _verificar_periodo_no_bloqueado(db, tenant_id, obj.anio, obj.mes)
        updated = MovimientoMensualRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, movimiento_id: UUID):
        obj = MovimientoMensualService.get_or_404(db, tenant_id, movimiento_id)
        if obj.estado == "cerrado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un movimiento cerrado."
            )
        _verificar_periodo_no_bloqueado(db, tenant_id, obj.anio, obj.mes)
        MovimientoMensualRepository.delete(db, obj)
        db.commit()

    # ── Conceptos ─────────────────────────────────────────────────────────────

    @staticmethod
    def list_conceptos(db: Session, tenant_id: UUID, movimiento_id: UUID):
        obj = MovimientoMensualService.get_or_404(db, tenant_id, movimiento_id)
        return MovimientoMensualRepository.get_conceptos(db, obj.id)

    @staticmethod
    def add_concepto(db: Session, tenant_id: UUID, movimiento_id: UUID,
                     body: MovimientoConceptoCreate):
        obj = MovimientoMensualService.get_or_404(db, tenant_id, movimiento_id)
        if obj.estado == "cerrado":
            raise HTTPException(status_code=400,
                                detail="No se puede modificar un movimiento cerrado.")
        _verificar_periodo_no_bloqueado(db, tenant_id, obj.anio, obj.mes)
        concepto = MovimientoMensualRepository.add_concepto(
            db, tenant_id, movimiento_id, body.model_dump()
        )
        db.commit()
        db.refresh(concepto)
        return concepto

    @staticmethod
    def update_concepto(db: Session, tenant_id: UUID, concepto_mov_id: UUID,
                        body: MovimientoConceptoUpdate):
        obj = MovimientoMensualRepository.get_concepto_by_id(db, tenant_id, concepto_mov_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Concepto de movimiento no encontrado.")
        updated = MovimientoMensualRepository.update_concepto(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete_concepto(db: Session, tenant_id: UUID, concepto_mov_id: UUID):
        obj = MovimientoMensualRepository.get_concepto_by_id(db, tenant_id, concepto_mov_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Concepto de movimiento no encontrado.")
        MovimientoMensualRepository.delete_concepto(db, obj)
        db.commit()

    @staticmethod
    def resumen_periodo(db: Session, tenant_id: UUID, anio: int, mes: int) -> dict:
        """Estadísticas del período: total trabajadores, estados, etc."""
        total = MovimientoMensualRepository.count_por_periodo(db, tenant_id, anio, mes)
        return {
            "anio": anio,
            "mes": mes,
            "total_trabajadores": total,
        }


# ─────────────────────────────────────────────────────────────────────────────
# FINIQUITO
# ─────────────────────────────────────────────────────────────────────────────

class FiniquitoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             trabajador_id: Optional[UUID], estado: Optional[str],
             anio: Optional[int]):
        return FiniquitoRepository.get_all(
            db, tenant_id, page, size, trabajador_id, estado, anio
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, finiquito_id: UUID):
        obj = FiniquitoRepository.get_by_id(db, tenant_id, finiquito_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Finiquito no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: FiniquitoCreate):
        obj = FiniquitoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, finiquito_id: UUID, body: FiniquitoUpdate):
        obj = FiniquitoService.get_or_404(db, tenant_id, finiquito_id)
        if obj.estado == "pagado":
            raise HTTPException(status_code=400,
                                detail="No se puede modificar un finiquito pagado.")
        # Validar que para firmar tenga causal y conceptos
        if body.estado == "firmado":
            if not obj.causal_id and not body.causal_id:
                raise HTTPException(status_code=400,
                                    detail="Debe especificar una causal antes de firmar.")
            conceptos = FiniquitoRepository.get_conceptos(db, finiquito_id)
            if not conceptos:
                raise HTTPException(status_code=400,
                                    detail="Debe agregar al menos un concepto antes de firmar.")
        updated = FiniquitoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    # ── Conceptos ─────────────────────────────────────────────────────────────

    @staticmethod
    def list_conceptos(db: Session, tenant_id: UUID, finiquito_id: UUID):
        FiniquitoService.get_or_404(db, tenant_id, finiquito_id)
        return FiniquitoRepository.get_conceptos(db, finiquito_id)

    @staticmethod
    def add_concepto(db: Session, tenant_id: UUID, finiquito_id: UUID,
                     body: FiniquitoConceptoCreate):
        obj = FiniquitoService.get_or_404(db, tenant_id, finiquito_id)
        if obj.estado == "pagado":
            raise HTTPException(status_code=400,
                                detail="No se puede modificar un finiquito pagado.")
        concepto = FiniquitoRepository.add_concepto(
            db, tenant_id, finiquito_id, body.model_dump()
        )
        # Recalcular total automáticamente
        totales = FiniquitoRepository.recalcular_total(db, finiquito_id)
        obj.total_finiquito = totales["total_finiquito"]
        db.commit()
        db.refresh(concepto)
        return concepto

    @staticmethod
    def delete_concepto(db: Session, tenant_id: UUID, finiquito_id: UUID,
                        concepto_id: UUID):
        obj = FiniquitoService.get_or_404(db, tenant_id, finiquito_id)
        if obj.estado == "pagado":
            raise HTTPException(status_code=400,
                                detail="No se puede modificar un finiquito pagado.")
        deleted = FiniquitoRepository.delete_concepto(db, tenant_id, concepto_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Concepto no encontrado.")
        # Recalcular total
        totales = FiniquitoRepository.recalcular_total(db, finiquito_id)
        obj.total_finiquito = totales["total_finiquito"]
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# PRÉSTAMO
# ─────────────────────────────────────────────────────────────────────────────

class PrestamoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             trabajador_id: Optional[UUID], estado: Optional[str]):
        return PrestamoRepository.get_all(
            db, tenant_id, page, size, trabajador_id, estado
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, prestamo_id: UUID):
        obj = PrestamoRepository.get_by_id(db, tenant_id, prestamo_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: PrestamoCreate):
        data = body.model_dump()
        obj = PrestamoRepository.create(db, tenant_id, data, generar_cuotas=True)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_cuotas(db: Session, tenant_id: UUID, prestamo_id: UUID,
                   solo_pendientes: bool = False):
        PrestamoService.get_or_404(db, tenant_id, prestamo_id)
        return PrestamoRepository.get_cuotas(db, prestamo_id, solo_pendientes)

    @staticmethod
    def update_cuota(db: Session, tenant_id: UUID, cuota_id: UUID,
                     body: PrestamoCuotaUpdate):
        cuota = PrestamoRepository.get_cuota(db, tenant_id, cuota_id)
        if not cuota:
            raise HTTPException(status_code=404, detail="Cuota no encontrada.")
        updated = PrestamoRepository.update_cuota(db, cuota, body.model_dump(exclude_unset=True))
        # Recalcular saldo del préstamo
        prestamo = PrestamoRepository.get_by_id(db, tenant_id, cuota.prestamo_id)
        if prestamo:
            PrestamoRepository.actualizar_saldo(db, prestamo)
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def pago_anticipado(db: Session, tenant_id: UUID, prestamo_id: UUID,
                        body: PagoAnticipadoRequest):
        prestamo = PrestamoService.get_or_404(db, tenant_id, prestamo_id)
        if prestamo.estado != "activo":
            raise HTTPException(status_code=400,
                                detail="Solo se pueden pagar cuotas de préstamos activos.")

        cuotas = PrestamoRepository.get_cuotas(db, prestamo_id)
        cuotas_dict = {c.nro_cuota: c for c in cuotas}

        for nro in body.nro_cuotas:
            cuota = cuotas_dict.get(nro)
            if not cuota:
                raise HTTPException(status_code=400,
                                    detail=f"Cuota {nro} no encontrada.")
            if cuota.pagada:
                raise HTTPException(status_code=400,
                                    detail=f"Cuota {nro} ya está pagada.")
            cuota.pagada = True
            from datetime import date
            cuota.fecha_pago = date.today()

        PrestamoRepository.actualizar_saldo(db, prestamo)
        db.commit()

        return {
            "prestamo_id": str(prestamo_id),
            "cuotas_pagadas": body.nro_cuotas,
            "saldo_pendiente": float(prestamo.saldo_pendiente),
            "estado": prestamo.estado,
        }

    @staticmethod
    def cancelar(db: Session, tenant_id: UUID, prestamo_id: UUID):
        prestamo = PrestamoService.get_or_404(db, tenant_id, prestamo_id)
        if prestamo.estado != "activo":
            raise HTTPException(status_code=400,
                                detail="Solo se pueden cancelar préstamos activos.")
        prestamo.estado = "cancelado"
        db.commit()
        db.refresh(prestamo)
        return prestamo


# ─────────────────────────────────────────────────────────────────────────────
# ANTICIPO
# ─────────────────────────────────────────────────────────────────────────────

class AnticipoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             trabajador_id: Optional[UUID], anio: Optional[int],
             mes: Optional[int], estado: Optional[str]):
        return AnticipoRepository.get_all(
            db, tenant_id, page, size, trabajador_id, anio, mes, estado
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, anticipo_id: UUID):
        obj = AnticipoRepository.get_by_id(db, tenant_id, anticipo_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Anticipo no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: AnticipoCreate):
        _verificar_periodo_no_bloqueado(db, tenant_id, body.anio, body.mes)
        obj = AnticipoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, anticipo_id: UUID, body: AnticipoUpdate):
        obj = AnticipoService.get_or_404(db, tenant_id, anticipo_id)
        if obj.estado == "anulado":
            raise HTTPException(status_code=400,
                                detail="No se puede modificar un anticipo anulado.")
        if obj.estado == "procesado" and body.monto:
            raise HTTPException(status_code=400,
                                detail="No se puede cambiar el monto de un anticipo procesado.")
        updated = AnticipoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def anular(db: Session, tenant_id: UUID, anticipo_id: UUID):
        obj = AnticipoService.get_or_404(db, tenant_id, anticipo_id)
        if obj.estado == "procesado":
            raise HTTPException(status_code=400,
                                detail="No se puede anular un anticipo ya procesado. "
                                       "Genere una nota de crédito.")
        if obj.estado == "anulado":
            raise HTTPException(status_code=400,
                                detail="El anticipo ya está anulado.")
        anulado = AnticipoRepository.anular(db, obj)
        db.commit()
        db.refresh(anulado)
        return anulado

    @staticmethod
    def resumen_periodo(db: Session, tenant_id: UUID, trabajador_id: UUID,
                        anio: int, mes: int) -> dict:
        total = AnticipoRepository.get_total_por_periodo(
            db, tenant_id, trabajador_id, anio, mes
        )
        return {
            "trabajador_id": str(trabajador_id),
            "anio": anio,
            "mes": mes,
            "total_anticipos_procesados": total,
        }
