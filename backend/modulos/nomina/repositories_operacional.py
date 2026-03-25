"""
modulos/nomina/repositories_operacional.py
==========================================
Repositorios para entidades operacionales de Nómina — Iteración 3.
Contrato, MovimientoMensual, Finiquito, Préstamo, Anticipo.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from modulos.nomina.models import (
    Anticipo, Contrato, ContratoClausula,
    Finiquito, FiniquitoConcepto,
    MovimientoConcepto, MovimientoMensual,
    Prestamo, PrestamoCuota,
)


def _set_tenant(db: Session, tenant_id: UUID) -> None:
    db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": str(tenant_id)})


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATO
# ─────────────────────────────────────────────────────────────────────────────

class ContratoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                trabajador_id: Optional[UUID] = None,
                estado: Optional[str] = None):
        _set_tenant(db, tenant_id)
        q = db.query(Contrato).filter(Contrato.tenant_id == tenant_id)
        if trabajador_id:
            q = q.filter(Contrato.trabajador_id == trabajador_id)
        if estado:
            q = q.filter(Contrato.estado == estado)
        total = q.count()
        items = q.order_by(Contrato.fecha_inicio.desc())\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, contrato_id: UUID) -> Optional[Contrato]:
        _set_tenant(db, tenant_id)
        return db.query(Contrato).filter(
            Contrato.tenant_id == tenant_id,
            Contrato.id == contrato_id
        ).first()

    @staticmethod
    def get_vigente_trabajador(db: Session, tenant_id: UUID,
                               trabajador_id: UUID) -> Optional[Contrato]:
        _set_tenant(db, tenant_id)
        return db.query(Contrato).filter(
            Contrato.tenant_id == tenant_id,
            Contrato.trabajador_id == trabajador_id,
            Contrato.estado == "vigente"
        ).order_by(Contrato.fecha_inicio.desc()).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Contrato:
        _set_tenant(db, tenant_id)
        clausula_ids = data.pop("clausula_ids", [])
        obj = Contrato(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        # Agregar cláusulas
        for cid in clausula_ids:
            cc = ContratoClausula(
                tenant_id=tenant_id,
                contrato_id=obj.id,
                clausula_id=cid
            )
            db.add(cc)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, obj: Contrato, data: dict) -> Contrato:
        clausula_ids = data.pop("clausula_ids", None)
        for k, v in data.items():
            setattr(obj, k, v)
        if clausula_ids is not None:
            # Reemplazar cláusulas
            db.query(ContratoClausula).filter(
                ContratoClausula.contrato_id == obj.id
            ).delete()
            for cid in clausula_ids:
                cc = ContratoClausula(
                    tenant_id=tenant_id,
                    contrato_id=obj.id,
                    clausula_id=cid
                )
                db.add(cc)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_clausulas(db: Session, contrato_id: UUID) -> list[ContratoClausula]:
        return db.query(ContratoClausula).filter(
            ContratoClausula.contrato_id == contrato_id
        ).all()


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO MENSUAL
# ─────────────────────────────────────────────────────────────────────────────

class MovimientoMensualRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                anio: Optional[int] = None, mes: Optional[int] = None,
                trabajador_id: Optional[UUID] = None,
                estado: Optional[str] = None):
        _set_tenant(db, tenant_id)
        q = db.query(MovimientoMensual).filter(MovimientoMensual.tenant_id == tenant_id)
        if anio:
            q = q.filter(MovimientoMensual.anio == anio)
        if mes:
            q = q.filter(MovimientoMensual.mes == mes)
        if trabajador_id:
            q = q.filter(MovimientoMensual.trabajador_id == trabajador_id)
        if estado:
            q = q.filter(MovimientoMensual.estado == estado)
        total = q.count()
        items = q.order_by(
            MovimientoMensual.anio.desc(),
            MovimientoMensual.mes.desc(),
            MovimientoMensual.nro_movimiento
        ).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID,
                  movimiento_id: UUID) -> Optional[MovimientoMensual]:
        _set_tenant(db, tenant_id)
        return db.query(MovimientoMensual).filter(
            MovimientoMensual.tenant_id == tenant_id,
            MovimientoMensual.id == movimiento_id
        ).first()

    @staticmethod
    def get_by_periodo_trabajador(db: Session, tenant_id: UUID,
                                   trabajador_id: UUID, anio: int,
                                   mes: int) -> list[MovimientoMensual]:
        _set_tenant(db, tenant_id)
        return db.query(MovimientoMensual).filter(
            MovimientoMensual.tenant_id == tenant_id,
            MovimientoMensual.trabajador_id == trabajador_id,
            MovimientoMensual.anio == anio,
            MovimientoMensual.mes == mes
        ).order_by(MovimientoMensual.nro_movimiento).all()

    @staticmethod
    def count_por_periodo(db: Session, tenant_id: UUID,
                          anio: int, mes: int) -> int:
        """Cuenta trabajadores con movimiento en el período."""
        _set_tenant(db, tenant_id)
        return db.query(func.count(MovimientoMensual.id)).filter(
            MovimientoMensual.tenant_id == tenant_id,
            MovimientoMensual.anio == anio,
            MovimientoMensual.mes == mes,
            MovimientoMensual.nro_movimiento == 1
        ).scalar()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> MovimientoMensual:
        _set_tenant(db, tenant_id)
        obj = MovimientoMensual(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: MovimientoMensual, data: dict) -> MovimientoMensual:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: MovimientoMensual) -> None:
        db.delete(obj)
        db.flush()

    # ── Conceptos del movimiento ──────────────────────────────────────────────

    @staticmethod
    def get_conceptos(db: Session, movimiento_id: UUID) -> list[MovimientoConcepto]:
        return db.query(MovimientoConcepto).filter(
            MovimientoConcepto.movimiento_id == movimiento_id
        ).all()

    @staticmethod
    def get_concepto_by_id(db: Session, tenant_id: UUID,
                           concepto_mov_id: UUID) -> Optional[MovimientoConcepto]:
        _set_tenant(db, tenant_id)
        return db.query(MovimientoConcepto).filter(
            MovimientoConcepto.tenant_id == tenant_id,
            MovimientoConcepto.id == concepto_mov_id
        ).first()

    @staticmethod
    def add_concepto(db: Session, tenant_id: UUID,
                     movimiento_id: UUID, data: dict) -> MovimientoConcepto:
        _set_tenant(db, tenant_id)
        obj = MovimientoConcepto(
            tenant_id=tenant_id,
            movimiento_id=movimiento_id,
            **data
        )
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_concepto(db: Session, obj: MovimientoConcepto,
                        data: dict) -> MovimientoConcepto:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_concepto(db: Session, obj: MovimientoConcepto) -> None:
        db.delete(obj)
        db.flush()

    @staticmethod
    def marcar_calculado(db: Session, obj: MovimientoMensual,
                         resultados: dict) -> MovimientoMensual:
        """Persiste los resultados del cálculo y marca como calculado."""
        from datetime import datetime, timezone
        for k, v in resultados.items():
            setattr(obj, k, v)
        obj.estado = "calculado"
        obj.calculado_en = datetime.now(timezone.utc)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# FINIQUITO
# ─────────────────────────────────────────────────────────────────────────────

class FiniquitoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                trabajador_id: Optional[UUID] = None,
                estado: Optional[str] = None,
                anio: Optional[int] = None):
        _set_tenant(db, tenant_id)
        q = db.query(Finiquito).filter(Finiquito.tenant_id == tenant_id)
        if trabajador_id:
            q = q.filter(Finiquito.trabajador_id == trabajador_id)
        if estado:
            q = q.filter(Finiquito.estado == estado)
        if anio:
            q = q.filter(
                func.extract("year", Finiquito.fecha_finiquito) == anio
            )
        total = q.count()
        items = q.order_by(Finiquito.fecha_finiquito.desc())\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID,
                  finiquito_id: UUID) -> Optional[Finiquito]:
        _set_tenant(db, tenant_id)
        return db.query(Finiquito).filter(
            Finiquito.tenant_id == tenant_id,
            Finiquito.id == finiquito_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Finiquito:
        _set_tenant(db, tenant_id)
        obj = Finiquito(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Finiquito, data: dict) -> Finiquito:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    # ── Conceptos del finiquito ────────────────────────────────────────────────

    @staticmethod
    def get_conceptos(db: Session, finiquito_id: UUID) -> list[FiniquitoConcepto]:
        return db.query(FiniquitoConcepto).filter(
            FiniquitoConcepto.finiquito_id == finiquito_id
        ).all()

    @staticmethod
    def add_concepto(db: Session, tenant_id: UUID,
                     finiquito_id: UUID, data: dict) -> FiniquitoConcepto:
        _set_tenant(db, tenant_id)
        obj = FiniquitoConcepto(
            tenant_id=tenant_id,
            finiquito_id=finiquito_id,
            **data
        )
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_concepto(db: Session, tenant_id: UUID,
                        concepto_id: UUID) -> bool:
        _set_tenant(db, tenant_id)
        obj = db.query(FiniquitoConcepto).filter(
            FiniquitoConcepto.id == concepto_id
        ).first()
        if obj:
            db.delete(obj)
            db.flush()
            return True
        return False

    @staticmethod
    def recalcular_total(db: Session, finiquito_id: UUID) -> dict:
        """Suma haberes y descuentos para obtener total neto."""
        conceptos = db.query(FiniquitoConcepto).filter(
            FiniquitoConcepto.finiquito_id == finiquito_id
        ).all()
        total_haberes = sum(c.monto for c in conceptos if c.es_haber)
        total_descuentos = sum(c.monto for c in conceptos if not c.es_haber)
        total_neto = total_haberes - total_descuentos
        return {
            "total_haberes": total_haberes,
            "total_descuentos": total_descuentos,
            "total_finiquito": total_neto
        }


# ─────────────────────────────────────────────────────────────────────────────
# PRÉSTAMO
# ─────────────────────────────────────────────────────────────────────────────

class PrestamoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                trabajador_id: Optional[UUID] = None,
                estado: Optional[str] = None):
        _set_tenant(db, tenant_id)
        q = db.query(Prestamo).filter(Prestamo.tenant_id == tenant_id)
        if trabajador_id:
            q = q.filter(Prestamo.trabajador_id == trabajador_id)
        if estado:
            q = q.filter(Prestamo.estado == estado)
        total = q.count()
        items = q.order_by(Prestamo.created_at.desc())\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID,
                  prestamo_id: UUID) -> Optional[Prestamo]:
        _set_tenant(db, tenant_id)
        return db.query(Prestamo).filter(
            Prestamo.tenant_id == tenant_id,
            Prestamo.id == prestamo_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict,
               generar_cuotas: bool = True) -> Prestamo:
        """Crea préstamo y genera automáticamente sus cuotas."""
        _set_tenant(db, tenant_id)
        from datetime import date
        from dateutil.relativedelta import relativedelta

        nro_cuotas = data["nro_cuotas"]
        valor_cuota = data["valor_cuota"]
        fecha_inicio = data["fecha_inicio"]
        monto_total = data["monto_total"]

        obj = Prestamo(
            tenant_id=tenant_id,
            saldo_pendiente=monto_total,
            **data
        )
        db.add(obj)
        db.flush()

        if generar_cuotas:
            for i in range(nro_cuotas):
                try:
                    fecha_cuota = fecha_inicio + relativedelta(months=i)
                except Exception:
                    # Fallback sin dateutil
                    mes = ((fecha_inicio.month - 1 + i) % 12) + 1
                    anio = fecha_inicio.year + ((fecha_inicio.month - 1 + i) // 12)
                    fecha_cuota = date(anio, mes, 1)

                cuota = PrestamoCuota(
                    tenant_id=tenant_id,
                    prestamo_id=obj.id,
                    nro_cuota=i + 1,
                    anio=fecha_cuota.year,
                    mes=fecha_cuota.month,
                    monto=valor_cuota,
                    procesar=True,
                    pagada=False,
                )
                db.add(cuota)

        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_cuotas(db: Session, prestamo_id: UUID,
                   solo_pendientes: bool = False) -> list[PrestamoCuota]:
        q = db.query(PrestamoCuota).filter(
            PrestamoCuota.prestamo_id == prestamo_id
        )
        if solo_pendientes:
            q = q.filter(PrestamoCuota.pagada == False)
        return q.order_by(PrestamoCuota.nro_cuota).all()

    @staticmethod
    def get_cuota(db: Session, tenant_id: UUID,
                  cuota_id: UUID) -> Optional[PrestamoCuota]:
        _set_tenant(db, tenant_id)
        return db.query(PrestamoCuota).filter(
            PrestamoCuota.tenant_id == tenant_id,
            PrestamoCuota.id == cuota_id
        ).first()

    @staticmethod
    def update_cuota(db: Session, obj: PrestamoCuota,
                     data: dict) -> PrestamoCuota:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def actualizar_saldo(db: Session, prestamo: Prestamo) -> Prestamo:
        """Recalcula saldo_pendiente en base a cuotas no pagadas."""
        pendiente = db.query(func.sum(PrestamoCuota.monto)).filter(
            PrestamoCuota.prestamo_id == prestamo.id,
            PrestamoCuota.pagada == False
        ).scalar() or 0
        prestamo.saldo_pendiente = pendiente
        if pendiente == 0:
            prestamo.estado = "cancelado"
        db.flush()
        db.refresh(prestamo)
        return prestamo


# ─────────────────────────────────────────────────────────────────────────────
# ANTICIPO
# ─────────────────────────────────────────────────────────────────────────────

class AnticipoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                trabajador_id: Optional[UUID] = None,
                anio: Optional[int] = None, mes: Optional[int] = None,
                estado: Optional[str] = None):
        _set_tenant(db, tenant_id)
        q = db.query(Anticipo).filter(Anticipo.tenant_id == tenant_id)
        if trabajador_id:
            q = q.filter(Anticipo.trabajador_id == trabajador_id)
        if anio:
            q = q.filter(Anticipo.anio == anio)
        if mes:
            q = q.filter(Anticipo.mes == mes)
        if estado:
            q = q.filter(Anticipo.estado == estado)
        total = q.count()
        items = q.order_by(Anticipo.fecha_emision.desc())\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID,
                  anticipo_id: UUID) -> Optional[Anticipo]:
        _set_tenant(db, tenant_id)
        return db.query(Anticipo).filter(
            Anticipo.tenant_id == tenant_id,
            Anticipo.id == anticipo_id
        ).first()

    @staticmethod
    def get_total_por_periodo(db: Session, tenant_id: UUID,
                              trabajador_id: UUID,
                              anio: int, mes: int) -> float:
        """Total de anticipos procesados en un período para un trabajador."""
        _set_tenant(db, tenant_id)
        result = db.query(func.sum(Anticipo.monto)).filter(
            Anticipo.tenant_id == tenant_id,
            Anticipo.trabajador_id == trabajador_id,
            Anticipo.anio == anio,
            Anticipo.mes == mes,
            Anticipo.estado == "procesado"
        ).scalar()
        return float(result or 0)

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Anticipo:
        _set_tenant(db, tenant_id)
        obj = Anticipo(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Anticipo, data: dict) -> Anticipo:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def anular(db: Session, obj: Anticipo) -> Anticipo:
        obj.estado = "anulado"
        db.flush()
        db.refresh(obj)
        return obj
