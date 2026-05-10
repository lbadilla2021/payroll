"""
modulos/rrhh/services.py
========================
Lógica de negocio para RRHH.
Orquesta repositorios, valida reglas de negocio y hace commit.
"""

from datetime import date as date_type
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from modulos.rrhh.repositories import (
    AtributoEvalCualitativaRepository, AtributoEvalCuantitativaRepository,
    CargaFamiliarRepository, CargoDesempenadoRepository,
    ConyugeAfiliadoRepository, EvaluacionCualitativaRepository,
    EvaluacionCuantitativaRepository, FichaPermisoRepository,
    FichaVacacionRepository, LicenciaMedicaRepository, ObservacionRepository,
    EstadoCivilRepository, TipoTrabajadorRepository, RegimenPrevisionalRepository,
    SupervisorRepository, TipoPermisoRepository,
    TrabajadorApvRepository, TrabajadorEvalRepository,
    TrabajadorRepository,
)
from modulos.rrhh.schemas import (
    AtributoEvalCualitativaCreate, AtributoEvalCualitativaUpdate,
    AtributoEvalCuantitativaCreate, AtributoEvalCuantitativaUpdate,
    CargaFamiliarCreate, CargaFamiliarUpdate,
    CargoDesempenadoCreate, CargoDesempenadoUpdate,
    ConyugeAfiliadoCreate, ConyugeAfiliadoUpdate,
    EvaluacionCualitativaCreate, EvaluacionCualitativaUpdate,
    EvaluacionCuantitativaCreate, EvaluacionCuantitativaUpdate,
    FichaPermisoCreate, FichaPermisoUpdate,
    FichaVacacionCreate, FichaVacacionUpdate,
    LicenciaMedicaCreate, LicenciaMedicaUpdate,
    ObservacionCreate, ObservacionUpdate,
    SupervisorCreate, SupervisorUpdate,
    TipoPermisoCreate, TipoPermisoUpdate,
    TrabajadorApvCreate, TrabajadorApvUpdate,
    TrabajadorCreate, TrabajadorUpdate,
    TrabajadorEvalCualitativaCreate, TrabajadorEvalCuantitativaCreate,
)


# ─────────────────────────────────────────────────────────────────────────────
# SUPERVISORES
# ─────────────────────────────────────────────────────────────────────────────

class SupervisorService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             search: str, solo_activos: bool):
        return SupervisorRepository.get_all(db, tenant_id, page, size, search, solo_activos)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, supervisor_id: UUID):
        obj = SupervisorRepository.get_by_id(db, tenant_id, supervisor_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Supervisor no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: SupervisorCreate):
        if SupervisorRepository.get_by_codigo(db, tenant_id, body.codigo):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Ya existe un supervisor con código '{body.codigo}'.")
        obj = SupervisorRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, supervisor_id: UUID, body: SupervisorUpdate):
        obj = SupervisorService.get_or_404(db, tenant_id, supervisor_id)
        updated = SupervisorRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, supervisor_id: UUID):
        obj = SupervisorService.get_or_404(db, tenant_id, supervisor_id)
        SupervisorRepository.delete(db, obj)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE PERMISO
# ─────────────────────────────────────────────────────────────────────────────

class TipoPermisoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int, solo_activos: bool):
        return TipoPermisoRepository.get_all(db, tenant_id, page, size, solo_activos)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, tipo_id: UUID):
        obj = TipoPermisoRepository.get_by_id(db, tenant_id, tipo_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Tipo de permiso no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: TipoPermisoCreate):
        obj = TipoPermisoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, tipo_id: UUID, body: TipoPermisoUpdate):
        obj = TipoPermisoService.get_or_404(db, tenant_id, tipo_id)
        updated = TipoPermisoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIONES (catálogos)
# ─────────────────────────────────────────────────────────────────────────────

class EvaluacionCuantitativaService:

    @staticmethod
    def list(db: Session, tenant_id: UUID):
        return EvaluacionCuantitativaRepository.get_all(db, tenant_id)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, eval_id: UUID):
        obj = EvaluacionCuantitativaRepository.get_by_id(db, tenant_id, eval_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Evaluación cuantitativa no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: EvaluacionCuantitativaCreate):
        obj = EvaluacionCuantitativaRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, eval_id: UUID, body: EvaluacionCuantitativaUpdate):
        obj = EvaluacionCuantitativaService.get_or_404(db, tenant_id, eval_id)
        updated = EvaluacionCuantitativaRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class AtributoEvalCuantitativaService:

    @staticmethod
    def list(db: Session, tenant_id: UUID):
        return AtributoEvalCuantitativaRepository.get_all(db, tenant_id)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, attr_id: UUID):
        obj = AtributoEvalCuantitativaRepository.get_by_id(db, tenant_id, attr_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Atributo no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: AtributoEvalCuantitativaCreate):
        obj = AtributoEvalCuantitativaRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, attr_id: UUID, body: AtributoEvalCuantitativaUpdate):
        obj = AtributoEvalCuantitativaService.get_or_404(db, tenant_id, attr_id)
        updated = AtributoEvalCuantitativaRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class EvaluacionCualitativaService:

    @staticmethod
    def list(db: Session, tenant_id: UUID):
        return EvaluacionCualitativaRepository.get_all(db, tenant_id)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, eval_id: UUID):
        obj = EvaluacionCualitativaRepository.get_by_id(db, tenant_id, eval_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Evaluación cualitativa no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: EvaluacionCualitativaCreate):
        obj = EvaluacionCualitativaRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, eval_id: UUID, body: EvaluacionCualitativaUpdate):
        obj = EvaluacionCualitativaService.get_or_404(db, tenant_id, eval_id)
        updated = EvaluacionCualitativaRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class AtributoEvalCualitativaService:

    @staticmethod
    def list(db: Session, tenant_id: UUID):
        return AtributoEvalCualitativaRepository.get_all(db, tenant_id)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, attr_id: UUID):
        obj = AtributoEvalCualitativaRepository.get_by_id(db, tenant_id, attr_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Atributo no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: AtributoEvalCualitativaCreate):
        obj = AtributoEvalCualitativaRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, attr_id: UUID, body: AtributoEvalCualitativaUpdate):
        obj = AtributoEvalCualitativaService.get_or_404(db, tenant_id, attr_id)
        updated = AtributoEvalCualitativaRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


# ─────────────────────────────────────────────────────────────────────────────
# TRABAJADOR
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int, search: str,
             solo_activos: bool, sucursal_id, centro_costo_id, cargo_id):
        return TrabajadorRepository.get_all(
            db, tenant_id, page, size, search, solo_activos,
            sucursal_id, centro_costo_id, cargo_id
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, trabajador_id: UUID):
        obj = TrabajadorRepository.get_by_id(db, tenant_id, trabajador_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Trabajador no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: TrabajadorCreate):
        if TrabajadorRepository.get_by_rut(db, tenant_id, body.rut):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Ya existe un trabajador con RUT '{body.rut}'.")
        if TrabajadorRepository.get_by_codigo(db, tenant_id, body.codigo):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Ya existe un trabajador con código '{body.codigo}'.")
        obj = TrabajadorRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, trabajador_id: UUID, body: TrabajadorUpdate):
        obj = TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        data = body.model_dump(exclude_unset=True)

        # Si cambia cargo_id, cerrar el vigente y abrir uno nuevo automáticamente
        nuevo_cargo_id = data.get('cargo_id')
        if nuevo_cargo_id and nuevo_cargo_id != obj.cargo_id:
            hoy = date_type.today()
            vigente = CargoDesempenadoRepository.get_latest_open(db, tenant_id, trabajador_id)
            if vigente:
                CargoDesempenadoRepository.update(db, vigente, {'fecha_hasta': hoy})
            CargoDesempenadoRepository.create(db, tenant_id, trabajador_id, {
                'cargo_id': nuevo_cargo_id,
                'cargo_descripcion': None,
                'fecha_desde': hoy,
                'fecha_hasta': None,
                'observaciones': None,
            })

        updated = TrabajadorRepository.update(db, obj, data)
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def deactivate(db: Session, tenant_id: UUID, trabajador_id: UUID):
        obj = TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj.es_activo = False
        db.commit()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# APV
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorApvService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return TrabajadorApvRepository.get_all(db, tenant_id, trabajador_id)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, apv_id: UUID):
        obj = TrabajadorApvRepository.get_by_id(db, tenant_id, apv_id)
        if not obj:
            raise HTTPException(status_code=404, detail="APV no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: TrabajadorApvCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = TrabajadorApvRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, apv_id: UUID, body: TrabajadorApvUpdate):
        obj = TrabajadorApvService.get_or_404(db, tenant_id, apv_id)
        updated = TrabajadorApvRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, apv_id: UUID):
        obj = TrabajadorApvService.get_or_404(db, tenant_id, apv_id)
        TrabajadorApvRepository.delete(db, obj)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# CÓNYUGE AFILIADO
# ─────────────────────────────────────────────────────────────────────────────

class ConyugeAfiliadoService:

    @staticmethod
    def get(db: Session, tenant_id: UUID, trabajador_id: UUID):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return ConyugeAfiliadoRepository.get(db, tenant_id, trabajador_id)

    @staticmethod
    def upsert(db: Session, tenant_id: UUID, trabajador_id: UUID, body: ConyugeAfiliadoCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        existing = ConyugeAfiliadoRepository.get(db, tenant_id, trabajador_id)
        if existing:
            updated = ConyugeAfiliadoRepository.update(db, existing, body.model_dump())
            db.commit()
            db.refresh(updated)
            return updated
        obj = ConyugeAfiliadoRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, trabajador_id: UUID, body: ConyugeAfiliadoUpdate):
        existing = ConyugeAfiliadoRepository.get(db, tenant_id, trabajador_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Datos de cónyuge no encontrados.")
        updated = ConyugeAfiliadoRepository.update(db, existing, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, trabajador_id: UUID):
        existing = ConyugeAfiliadoRepository.get(db, tenant_id, trabajador_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Datos de cónyuge no encontrados.")
        ConyugeAfiliadoRepository.delete(db, existing)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# CARGAS FAMILIARES
# ─────────────────────────────────────────────────────────────────────────────

class CargaFamiliarService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID, solo_activas: bool):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return CargaFamiliarRepository.get_all(db, tenant_id, trabajador_id, solo_activas)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, carga_id: UUID):
        obj = CargaFamiliarRepository.get_by_id(db, tenant_id, carga_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Carga familiar no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: CargaFamiliarCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = CargaFamiliarRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, carga_id: UUID, body: CargaFamiliarUpdate):
        obj = CargaFamiliarService.get_or_404(db, tenant_id, carga_id)
        updated = CargaFamiliarRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


# ─────────────────────────────────────────────────────────────────────────────
# FICHA VACACIONES
# ─────────────────────────────────────────────────────────────────────────────

class FichaVacacionService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int, size: int):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return FichaVacacionRepository.get_all(db, tenant_id, trabajador_id, page, size)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, vac_id: UUID):
        obj = FichaVacacionRepository.get_by_id(db, tenant_id, vac_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Registro de vacaciones no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: FichaVacacionCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = FichaVacacionRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, vac_id: UUID, body: FichaVacacionUpdate):
        obj = FichaVacacionService.get_or_404(db, tenant_id, vac_id)
        updated = FichaVacacionRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, vac_id: UUID):
        obj = FichaVacacionService.get_or_404(db, tenant_id, vac_id)
        FichaVacacionRepository.delete(db, obj)
        db.commit()

    @staticmethod
    def resumen_dias(db: Session, tenant_id: UUID, trabajador_id: UUID) -> dict:
        return FichaVacacionRepository.resumen(db, tenant_id, trabajador_id)


# ─────────────────────────────────────────────────────────────────────────────
# FICHA PERMISOS
# ─────────────────────────────────────────────────────────────────────────────

class FichaPermisoService:

    @staticmethod
    def _enrich(items: list) -> list:
        for p in items:
            p.tipo_permiso_nombre = p.tipo_permiso.descripcion if p.tipo_permiso else None
        return items

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int, size: int):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        items, total = FichaPermisoRepository.get_all(db, tenant_id, trabajador_id, page, size)
        return FichaPermisoService._enrich(items), total

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, permiso_id: UUID):
        obj = FichaPermisoRepository.get_by_id(db, tenant_id, permiso_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Permiso no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: FichaPermisoCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = FichaPermisoRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        FichaPermisoService._enrich([obj])
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, permiso_id: UUID, body: FichaPermisoUpdate):
        obj = FichaPermisoService.get_or_404(db, tenant_id, permiso_id)
        updated = FichaPermisoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        FichaPermisoService._enrich([updated])
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, permiso_id: UUID):
        obj = FichaPermisoService.get_or_404(db, tenant_id, permiso_id)
        FichaPermisoRepository.delete(db, obj)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# OBSERVACIONES
# ─────────────────────────────────────────────────────────────────────────────

class ObservacionService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int, size: int):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return ObservacionRepository.get_all(db, tenant_id, trabajador_id, page, size)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, obs_id: UUID):
        obj = ObservacionRepository.get_by_id(db, tenant_id, obs_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Observación no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: ObservacionCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = ObservacionRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, obs_id: UUID, body: ObservacionUpdate):
        obj = ObservacionService.get_or_404(db, tenant_id, obs_id)
        updated = ObservacionRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, obs_id: UUID):
        obj = ObservacionService.get_or_404(db, tenant_id, obs_id)
        ObservacionRepository.delete(db, obj)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# CARGOS DESEMPEÑADOS
# ─────────────────────────────────────────────────────────────────────────────

class CargoDesempenadoService:

    @staticmethod
    def _enrich(db: Session, items: list) -> list:
        """Agrega cargo_nombre consultando nomina.cargo."""
        from modulos.nomina.models import Cargo
        ids = [i.cargo_id for i in items if i.cargo_id]
        nombres = {}
        if ids:
            nombres = {c.id: c.descripcion
                       for c in db.query(Cargo).filter(Cargo.id.in_(ids)).all()}
        for item in items:
            item.cargo_nombre = nombres.get(item.cargo_id) if item.cargo_id else None
        return items

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        items = CargoDesempenadoRepository.get_all(db, tenant_id, trabajador_id)
        return CargoDesempenadoService._enrich(db, items)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, cargo_id: UUID):
        obj = CargoDesempenadoRepository.get_by_id(db, tenant_id, cargo_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Cargo desempeñado no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: CargoDesempenadoCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = CargoDesempenadoRepository.create(db, tenant_id, trabajador_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        CargoDesempenadoService._enrich(db, [obj])
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, cargo_id: UUID, body: CargoDesempenadoUpdate):
        obj = CargoDesempenadoService.get_or_404(db, tenant_id, cargo_id)
        updated = CargoDesempenadoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        CargoDesempenadoService._enrich(db, [updated])
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, cargo_id: UUID):
        obj = CargoDesempenadoService.get_or_404(db, tenant_id, cargo_id)
        CargoDesempenadoRepository.delete(db, obj)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIONES DEL TRABAJADOR
# ─────────────────────────────────────────────────────────────────────────────

class TrabajadorEvalService:

    @staticmethod
    def list_cuantitativas(db: Session, tenant_id: UUID, trabajador_id: UUID):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return TrabajadorEvalRepository.get_cuantitativas(db, tenant_id, trabajador_id)

    @staticmethod
    def create_cuantitativa(db: Session, tenant_id: UUID, trabajador_id: UUID,
                            actor_id: UUID, body: TrabajadorEvalCuantitativaCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = TrabajadorEvalRepository.create_cuantitativa(
            db, tenant_id, trabajador_id, actor_id, body.model_dump()
        )
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_cualitativas(db: Session, tenant_id: UUID, trabajador_id: UUID):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return TrabajadorEvalRepository.get_cualitativas(db, tenant_id, trabajador_id)

    @staticmethod
    def create_cualitativa(db: Session, tenant_id: UUID, trabajador_id: UUID,
                           actor_id: UUID, body: TrabajadorEvalCualitativaCreate):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        obj = TrabajadorEvalRepository.create_cualitativa(
            db, tenant_id, trabajador_id, actor_id, body.model_dump()
        )
        db.commit()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# MANTENEDORES GLOBALES
# ─────────────────────────────────────────────────────────────────────────────

class _MantenedorGlobalService:
    """Servicio genérico para catálogos globales sin tenant."""

    def __init__(self, repo, nombre: str):
        self._repo   = repo
        self._nombre = nombre

    def list(self, db: Session) -> list:
        return self._repo.get_all(db)

    def get_or_404(self, db: Session, item_id: int):
        obj = self._repo.get_by_id(db, item_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"{self._nombre} no encontrado.")
        return obj

    def create(self, db: Session, data: dict):
        if self._repo.get_by_codigo(db, data["codigo"]):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Ya existe un registro con código {data['codigo']}.")
        obj = self._repo.create(db, data)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, item_id: int, data: dict):
        obj = self.get_or_404(db, item_id)
        obj = self._repo.update(db, obj, {k: v for k, v in data.items() if v is not None})
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, item_id: int) -> None:
        obj = self.get_or_404(db, item_id)
        self._repo.delete(db, obj)
        db.commit()


EstadoCivilService       = _MantenedorGlobalService(EstadoCivilRepository,       "Estado civil")
TipoTrabajadorService    = _MantenedorGlobalService(TipoTrabajadorRepository,    "Tipo de trabajador")
RegimenPrevisionalService = _MantenedorGlobalService(RegimenPrevisionalRepository, "Régimen previsional")


# ─────────────────────────────────────────────────────────────────────────────
# LICENCIAS MÉDICAS
# ─────────────────────────────────────────────────────────────────────────────

class LicenciaMedicaService:

    @staticmethod
    def _fecha_termino(fecha_inicio, dias: int):
        from datetime import timedelta
        return fecha_inicio + timedelta(days=dias - 1)

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int = 1, size: int = 50):
        return LicenciaMedicaRepository.get_all(db, tenant_id, trabajador_id, page, size)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, lic_id: UUID):
        obj = LicenciaMedicaRepository.get_by_id(db, tenant_id, lic_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Licencia médica no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, trabajador_id: UUID, body: LicenciaMedicaCreate):
        data = body.model_dump()
        data["fecha_termino"] = LicenciaMedicaService._fecha_termino(data["fecha_inicio"], data["dias"])
        obj = LicenciaMedicaRepository.create(db, tenant_id, trabajador_id, data)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, lic_id: UUID, body: LicenciaMedicaUpdate):
        obj = LicenciaMedicaService.get_or_404(db, tenant_id, lic_id)
        data = body.model_dump(exclude_unset=True)
        fecha_inicio = data.get("fecha_inicio", obj.fecha_inicio)
        dias = data.get("dias", obj.dias)
        data["fecha_termino"] = LicenciaMedicaService._fecha_termino(fecha_inicio, dias)
        updated = LicenciaMedicaRepository.update(db, obj, data)
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, lic_id: UUID) -> None:
        obj = LicenciaMedicaService.get_or_404(db, tenant_id, lic_id)
        LicenciaMedicaRepository.delete(db, obj)
        db.commit()
