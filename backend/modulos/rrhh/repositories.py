"""
modulos/rrhh/repositories.py
============================
Capa de acceso a datos para RRHH.
Todas las operaciones son tenant-scoped.
El RLS se activa con SET LOCAL antes de cada operación.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from modulos.rrhh.models import (
    AtributoEvalCualitativa, AtributoEvalCuantitativa,
    CargaFamiliar, CargoDesempenado,
    EvaluacionCualitativa, EvaluacionCuantitativa,
    FichaPermiso, FichaPrestamo, FichaVacacion,
    Observacion, Supervisor, TipoPermiso,
    Trabajador, TrabajadorApv, TrabajadorConyugeAfiliado,
    TrabajadorEvalCualitativa, TrabajadorEvalCuantitativa,
)


def _set_tenant(db: Session, tenant_id: UUID) -> None:
    """Activa RLS para la sesión actual."""
    db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": str(tenant_id)})


# ─────────────────────────────────────────────────────────────────────────────
# SUPERVISORES
# ─────────────────────────────────────────────────────────────────────────────

class SupervisorRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                search: str = "", solo_activos: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(Supervisor).filter(Supervisor.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(Supervisor.es_activo == True)
        if search:
            q = q.filter(Supervisor.nombre.ilike(f"%{search}%"))
        total = q.count()
        items = q.order_by(Supervisor.nombre).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, supervisor_id: UUID) -> Optional[Supervisor]:
        _set_tenant(db, tenant_id)
        return db.query(Supervisor).filter(
            Supervisor.tenant_id == tenant_id,
            Supervisor.id == supervisor_id
        ).first()

    @staticmethod
    def get_by_codigo(db: Session, tenant_id: UUID, codigo: str) -> Optional[Supervisor]:
        _set_tenant(db, tenant_id)
        return db.query(Supervisor).filter(
            Supervisor.tenant_id == tenant_id,
            Supervisor.codigo == codigo
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Supervisor:
        _set_tenant(db, tenant_id)
        obj = Supervisor(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Supervisor, data: dict) -> Supervisor:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Supervisor) -> None:
        db.delete(obj)
        db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE PERMISO
# ─────────────────────────────────────────────────────────────────────────────

class TipoPermisoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 50,
                solo_activos: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(TipoPermiso).filter(TipoPermiso.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(TipoPermiso.es_activo == True)
        total = q.count()
        items = q.order_by(TipoPermiso.descripcion).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, tipo_id: UUID) -> Optional[TipoPermiso]:
        _set_tenant(db, tenant_id)
        return db.query(TipoPermiso).filter(
            TipoPermiso.tenant_id == tenant_id,
            TipoPermiso.id == tipo_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> TipoPermiso:
        _set_tenant(db, tenant_id)
        obj = TipoPermiso(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: TipoPermiso, data: dict) -> TipoPermiso:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS EVALUACIONES
# ─────────────────────────────────────────────────────────────────────────────

class EvaluacionCuantitativaRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(EvaluacionCuantitativa).filter(
            EvaluacionCuantitativa.tenant_id == tenant_id
        ).order_by(EvaluacionCuantitativa.descripcion).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, eval_id: UUID) -> Optional[EvaluacionCuantitativa]:
        _set_tenant(db, tenant_id)
        return db.query(EvaluacionCuantitativa).filter(
            EvaluacionCuantitativa.tenant_id == tenant_id,
            EvaluacionCuantitativa.id == eval_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> EvaluacionCuantitativa:
        _set_tenant(db, tenant_id)
        obj = EvaluacionCuantitativa(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: EvaluacionCuantitativa, data: dict) -> EvaluacionCuantitativa:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class AtributoEvalCuantitativaRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(AtributoEvalCuantitativa).filter(
            AtributoEvalCuantitativa.tenant_id == tenant_id
        ).order_by(AtributoEvalCuantitativa.descripcion).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, attr_id: UUID) -> Optional[AtributoEvalCuantitativa]:
        _set_tenant(db, tenant_id)
        return db.query(AtributoEvalCuantitativa).filter(
            AtributoEvalCuantitativa.tenant_id == tenant_id,
            AtributoEvalCuantitativa.id == attr_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> AtributoEvalCuantitativa:
        _set_tenant(db, tenant_id)
        obj = AtributoEvalCuantitativa(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: AtributoEvalCuantitativa, data: dict) -> AtributoEvalCuantitativa:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class EvaluacionCualitativaRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(EvaluacionCualitativa).filter(
            EvaluacionCualitativa.tenant_id == tenant_id
        ).order_by(EvaluacionCualitativa.descripcion).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, eval_id: UUID) -> Optional[EvaluacionCualitativa]:
        _set_tenant(db, tenant_id)
        return db.query(EvaluacionCualitativa).filter(
            EvaluacionCualitativa.tenant_id == tenant_id,
            EvaluacionCualitativa.id == eval_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> EvaluacionCualitativa:
        _set_tenant(db, tenant_id)
        obj = EvaluacionCualitativa(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: EvaluacionCualitativa, data: dict) -> EvaluacionCualitativa:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class AtributoEvalCualitativaRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(AtributoEvalCualitativa).filter(
            AtributoEvalCualitativa.tenant_id == tenant_id
        ).order_by(AtributoEvalCualitativa.descripcion).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, attr_id: UUID) -> Optional[AtributoEvalCualitativa]:
        _set_tenant(db, tenant_id)
        return db.query(AtributoEvalCualitativa).filter(
            AtributoEvalCualitativa.tenant_id == tenant_id,
            AtributoEvalCualitativa.id == attr_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> AtributoEvalCualitativa:
        _set_tenant(db, tenant_id)
        obj = AtributoEvalCualitativa(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: AtributoEvalCualitativa, data: dict) -> AtributoEvalCualitativa:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# TRABAJADOR
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 20,
                search: str = "", solo_activos: bool = True,
                sucursal_id: Optional[UUID] = None,
                centro_costo_id: Optional[UUID] = None,
                cargo_id: Optional[UUID] = None):
        _set_tenant(db, tenant_id)
        q = db.query(Trabajador).filter(Trabajador.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(Trabajador.es_activo == True)
        if search:
            q = q.filter(
                Trabajador.nombres.ilike(f"%{search}%") |
                Trabajador.apellido_paterno.ilike(f"%{search}%") |
                Trabajador.rut.ilike(f"%{search}%") |
                Trabajador.codigo.ilike(f"%{search}%")
            )
        if sucursal_id:
            q = q.filter(Trabajador.sucursal_id == sucursal_id)
        if centro_costo_id:
            q = q.filter(Trabajador.centro_costo_id == centro_costo_id)
        if cargo_id:
            q = q.filter(Trabajador.cargo_id == cargo_id)
        total = q.count()
        items = q.order_by(Trabajador.apellido_paterno, Trabajador.nombres)\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, trabajador_id: UUID) -> Optional[Trabajador]:
        _set_tenant(db, tenant_id)
        return db.query(Trabajador).filter(
            Trabajador.tenant_id == tenant_id,
            Trabajador.id == trabajador_id
        ).first()

    @staticmethod
    def get_by_rut(db: Session, tenant_id: UUID, rut: str) -> Optional[Trabajador]:
        _set_tenant(db, tenant_id)
        return db.query(Trabajador).filter(
            Trabajador.tenant_id == tenant_id,
            Trabajador.rut == rut
        ).first()

    @staticmethod
    def get_by_codigo(db: Session, tenant_id: UUID, codigo: str) -> Optional[Trabajador]:
        _set_tenant(db, tenant_id)
        return db.query(Trabajador).filter(
            Trabajador.tenant_id == tenant_id,
            Trabajador.codigo == codigo
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Trabajador:
        _set_tenant(db, tenant_id)
        obj = Trabajador(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Trabajador, data: dict) -> Trabajador:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# APV
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorApvRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, trabajador_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(TrabajadorApv).filter(
            TrabajadorApv.tenant_id == tenant_id,
            TrabajadorApv.trabajador_id == trabajador_id
        ).order_by(TrabajadorApv.fecha_inicio.desc()).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, apv_id: UUID) -> Optional[TrabajadorApv]:
        _set_tenant(db, tenant_id)
        return db.query(TrabajadorApv).filter(
            TrabajadorApv.tenant_id == tenant_id,
            TrabajadorApv.id == apv_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, data: dict) -> TrabajadorApv:
        _set_tenant(db, tenant_id)
        obj = TrabajadorApv(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: TrabajadorApv, data: dict) -> TrabajadorApv:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: TrabajadorApv) -> None:
        db.delete(obj)
        db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# CÓNYUGE AFILIADO
# ─────────────────────────────────────────────────────────────────────────────

class ConyugeAfiliadoRepository:

    @staticmethod
    def get(db: Session, tenant_id: UUID, trabajador_id: UUID) -> Optional[TrabajadorConyugeAfiliado]:
        _set_tenant(db, tenant_id)
        return db.query(TrabajadorConyugeAfiliado).filter(
            TrabajadorConyugeAfiliado.tenant_id == tenant_id,
            TrabajadorConyugeAfiliado.trabajador_id == trabajador_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID,
               data: dict) -> TrabajadorConyugeAfiliado:
        _set_tenant(db, tenant_id)
        obj = TrabajadorConyugeAfiliado(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: TrabajadorConyugeAfiliado, data: dict) -> TrabajadorConyugeAfiliado:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: TrabajadorConyugeAfiliado) -> None:
        db.delete(obj)
        db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# CARGAS FAMILIARES
# ─────────────────────────────────────────────────────────────────────────────

class CargaFamiliarRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, trabajador_id: UUID, solo_activas: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(CargaFamiliar).filter(
            CargaFamiliar.tenant_id == tenant_id,
            CargaFamiliar.trabajador_id == trabajador_id
        )
        if solo_activas:
            q = q.filter(CargaFamiliar.es_activa == True)
        return q.order_by(CargaFamiliar.fecha_nacimiento).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, carga_id: UUID) -> Optional[CargaFamiliar]:
        _set_tenant(db, tenant_id)
        return db.query(CargaFamiliar).filter(
            CargaFamiliar.tenant_id == tenant_id,
            CargaFamiliar.id == carga_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, data: dict) -> CargaFamiliar:
        _set_tenant(db, tenant_id)
        obj = CargaFamiliar(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: CargaFamiliar, data: dict) -> CargaFamiliar:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# FICHA VACACIONES
# ─────────────────────────────────────────────────────────────────────────────

class FichaVacacionRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int = 1, size: int = 50):
        _set_tenant(db, tenant_id)
        q = db.query(FichaVacacion).filter(
            FichaVacacion.tenant_id == tenant_id,
            FichaVacacion.trabajador_id == trabajador_id
        )
        total = q.count()
        items = q.order_by(FichaVacacion.fecha_desde.desc()).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, vac_id: UUID) -> Optional[FichaVacacion]:
        _set_tenant(db, tenant_id)
        return db.query(FichaVacacion).filter(
            FichaVacacion.tenant_id == tenant_id,
            FichaVacacion.id == vac_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, data: dict) -> FichaVacacion:
        _set_tenant(db, tenant_id)
        obj = FichaVacacion(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: FichaVacacion, data: dict) -> FichaVacacion:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: FichaVacacion) -> None:
        db.delete(obj)
        db.flush()

    @staticmethod
    def total_dias_utilizados(db: Session, tenant_id: UUID, trabajador_id: UUID) -> float:
        _set_tenant(db, tenant_id)
        result = db.query(func.sum(FichaVacacion.dias_utilizados)).filter(
            FichaVacacion.tenant_id == tenant_id,
            FichaVacacion.trabajador_id == trabajador_id
        ).scalar()
        return float(result or 0)


# ─────────────────────────────────────────────────────────────────────────────
# FICHA PERMISOS
# ─────────────────────────────────────────────────────────────────────────────

class FichaPermisoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int = 1, size: int = 50):
        _set_tenant(db, tenant_id)
        q = db.query(FichaPermiso).filter(
            FichaPermiso.tenant_id == tenant_id,
            FichaPermiso.trabajador_id == trabajador_id
        )
        total = q.count()
        items = q.order_by(FichaPermiso.fecha_desde.desc()).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, permiso_id: UUID) -> Optional[FichaPermiso]:
        _set_tenant(db, tenant_id)
        return db.query(FichaPermiso).filter(
            FichaPermiso.tenant_id == tenant_id,
            FichaPermiso.id == permiso_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, data: dict) -> FichaPermiso:
        _set_tenant(db, tenant_id)
        obj = FichaPermiso(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: FichaPermiso, data: dict) -> FichaPermiso:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: FichaPermiso) -> None:
        db.delete(obj)
        db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# OBSERVACIONES
# ─────────────────────────────────────────────────────────────────────────────

class ObservacionRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int = 1, size: int = 50):
        _set_tenant(db, tenant_id)
        q = db.query(Observacion).filter(
            Observacion.tenant_id == tenant_id,
            Observacion.trabajador_id == trabajador_id
        )
        total = q.count()
        items = q.order_by(Observacion.fecha_evento.desc()).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, obs_id: UUID) -> Optional[Observacion]:
        _set_tenant(db, tenant_id)
        return db.query(Observacion).filter(
            Observacion.tenant_id == tenant_id,
            Observacion.id == obs_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, data: dict) -> Observacion:
        _set_tenant(db, tenant_id)
        obj = Observacion(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Observacion, data: dict) -> Observacion:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Observacion) -> None:
        db.delete(obj)
        db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# CARGOS DESEMPEÑADOS
# ─────────────────────────────────────────────────────────────────────────────

class CargoDesempenadoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, trabajador_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(CargoDesempenado).filter(
            CargoDesempenado.tenant_id == tenant_id,
            CargoDesempenado.trabajador_id == trabajador_id
        ).order_by(CargoDesempenado.fecha_desde.desc()).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, cargo_id: UUID) -> Optional[CargoDesempenado]:
        _set_tenant(db, tenant_id)
        return db.query(CargoDesempenado).filter(
            CargoDesempenado.tenant_id == tenant_id,
            CargoDesempenado.id == cargo_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, data: dict) -> CargoDesempenado:
        _set_tenant(db, tenant_id)
        obj = CargoDesempenado(tenant_id=tenant_id, trabajador_id=trabajador_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: CargoDesempenado, data: dict) -> CargoDesempenado:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIONES DEL TRABAJADOR
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorEvalRepository:

    @staticmethod
    def get_cuantitativas(db: Session, tenant_id: UUID, trabajador_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(TrabajadorEvalCuantitativa).filter(
            TrabajadorEvalCuantitativa.tenant_id == tenant_id,
            TrabajadorEvalCuantitativa.trabajador_id == trabajador_id
        ).order_by(TrabajadorEvalCuantitativa.fecha_evaluacion.desc()).all()

    @staticmethod
    def create_cuantitativa(db: Session, tenant_id: UUID, trabajador_id: UUID,
                            actor_id: UUID, data: dict) -> TrabajadorEvalCuantitativa:
        _set_tenant(db, tenant_id)
        obj = TrabajadorEvalCuantitativa(
            tenant_id=tenant_id,
            trabajador_id=trabajador_id,
            creado_por_id=actor_id,
            **data
        )
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_cualitativas(db: Session, tenant_id: UUID, trabajador_id: UUID):
        _set_tenant(db, tenant_id)
        return db.query(TrabajadorEvalCualitativa).filter(
            TrabajadorEvalCualitativa.tenant_id == tenant_id,
            TrabajadorEvalCualitativa.trabajador_id == trabajador_id
        ).order_by(TrabajadorEvalCualitativa.fecha_evaluacion.desc()).all()

    @staticmethod
    def create_cualitativa(db: Session, tenant_id: UUID, trabajador_id: UUID,
                           actor_id: UUID, data: dict) -> TrabajadorEvalCualitativa:
        _set_tenant(db, tenant_id)
        obj = TrabajadorEvalCualitativa(
            tenant_id=tenant_id,
            trabajador_id=trabajador_id,
            creado_por_id=actor_id,
            **data
        )
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj
