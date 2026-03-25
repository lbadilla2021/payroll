"""
modulos/rrhh/services.py
========================
Lógica de negocio para RRHH.
Orquesta repositorios, valida reglas de negocio y hace commit.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from modulos.rrhh.repositories import (
    AtributoEvalCualitativaRepository, AtributoEvalCuantitativaRepository,
    CargaFamiliarRepository, CargoDesempenadoRepository,
    ConyugeAfiliadoRepository, EvaluacionCualitativaRepository,
    EvaluacionCuantitativaRepository, FichaPermisoRepository,
    FichaVacacionRepository, ObservacionRepository,
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
        updated = TrabajadorRepository.update(db, obj, body.model_dump(exclude_unset=True))
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
        total_utilizados = FichaVacacionRepository.total_dias_utilizados(db, tenant_id, trabajador_id)
        return {"total_dias_utilizados": total_utilizados}


# ─────────────────────────────────────────────────────────────────────────────
# FICHA PERMISOS
# ─────────────────────────────────────────────────────────────────────────────

class FichaPermisoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID, page: int, size: int):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return FichaPermisoRepository.get_all(db, tenant_id, trabajador_id, page, size)

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
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, permiso_id: UUID, body: FichaPermisoUpdate):
        obj = FichaPermisoService.get_or_404(db, tenant_id, permiso_id)
        updated = FichaPermisoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
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
    def list(db: Session, tenant_id: UUID, trabajador_id: UUID):
        TrabajadorService.get_or_404(db, tenant_id, trabajador_id)
        return CargoDesempenadoRepository.get_all(db, tenant_id, trabajador_id)

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
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, cargo_id: UUID, body: CargoDesempenadoUpdate):
        obj = CargoDesempenadoService.get_or_404(db, tenant_id, cargo_id)
        updated = CargoDesempenadoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


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
