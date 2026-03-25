"""
modulos/rrhh/endpoints.py
=========================
Rutas FastAPI para el módulo RRHH.
Todas las rutas son tenant-scoped vía require_permission o require_admin_or_superadmin.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.models.models import User

from modulos.rrhh.schemas import (
    AtributoEvalCualitativaCreate, AtributoEvalCualitativaRead, AtributoEvalCualitativaUpdate,
    AtributoEvalCuantitativaCreate, AtributoEvalCuantitativaRead, AtributoEvalCuantitativaUpdate,
    CargaFamiliarCreate, CargaFamiliarList, CargaFamiliarRead, CargaFamiliarUpdate,
    CargoDesempenadoCreate, CargoDesempenadoRead, CargoDesempenadoUpdate,
    ConyugeAfiliadoCreate, ConyugeAfiliadoRead, ConyugeAfiliadoUpdate,
    EvaluacionCualitativaCreate, EvaluacionCualitativaRead, EvaluacionCualitativaUpdate,
    EvaluacionCuantitativaCreate, EvaluacionCuantitativaRead, EvaluacionCuantitativaUpdate,
    FichaPermisoCreate, FichaPermisoList, FichaPermisoRead, FichaPermisoUpdate,
    FichaVacacionCreate, FichaVacacionList, FichaVacacionRead, FichaVacacionUpdate,
    ObservacionCreate, ObservacionList, ObservacionRead, ObservacionUpdate,
    SupervisorCreate, SupervisorList, SupervisorRead, SupervisorUpdate,
    TipoPermisoCreate, TipoPermisoList, TipoPermisoRead, TipoPermisoUpdate,
    TrabajadorApvCreate, TrabajadorApvRead, TrabajadorApvUpdate,
    TrabajadorCreate, TrabajadorList, TrabajadorListItem, TrabajadorRead, TrabajadorUpdate,
    TrabajadorEvalCualitativaCreate, TrabajadorEvalCualitativaRead,
    TrabajadorEvalCuantitativaCreate, TrabajadorEvalCuantitativaRead,
)
from modulos.rrhh.services import (
    AtributoEvalCualitativaService, AtributoEvalCuantitativaService,
    CargaFamiliarService, CargoDesempenadoService,
    ConyugeAfiliadoService, EvaluacionCualitativaService,
    EvaluacionCuantitativaService, FichaPermisoService,
    FichaVacacionService, ObservacionService,
    SupervisorService, TipoPermisoService,
    TrabajadorApvService, TrabajadorEvalService, TrabajadorService,
)


def _tenant_id(actor: User) -> UUID:
    """Extrae tenant_id del usuario autenticado."""
    return actor.tenant_id


# ─────────────────────────────────────────────────────────────────────────────
# SUPERVISORES
# ─────────────────────────────────────────────────────────────────────────────

router_supervisores = APIRouter(prefix="/rrhh/supervisores", tags=["RRHH - Supervisores"])


@router_supervisores.get("", response_model=SupervisorList)
def list_supervisores(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.supervisores.read")),
):
    items, total = SupervisorService.list(db, _tenant_id(actor), page, size, search, solo_activos)
    return SupervisorList(items=[SupervisorRead.model_validate(i) for i in items],
                          total=total, page=page, size=size)


@router_supervisores.post("", response_model=SupervisorRead, status_code=status.HTTP_201_CREATED)
def create_supervisor(
    body: SupervisorCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.supervisores.create")),
):
    obj = SupervisorService.create(db, _tenant_id(actor), body)
    return SupervisorRead.model_validate(obj)


@router_supervisores.get("/{supervisor_id}", response_model=SupervisorRead)
def get_supervisor(
    supervisor_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.supervisores.read")),
):
    obj = SupervisorService.get_or_404(db, _tenant_id(actor), supervisor_id)
    return SupervisorRead.model_validate(obj)


@router_supervisores.patch("/{supervisor_id}", response_model=SupervisorRead)
def update_supervisor(
    supervisor_id: UUID,
    body: SupervisorUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.supervisores.update")),
):
    obj = SupervisorService.update(db, _tenant_id(actor), supervisor_id, body)
    return SupervisorRead.model_validate(obj)


@router_supervisores.delete("/{supervisor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supervisor(
    supervisor_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.supervisores.delete")),
):
    SupervisorService.delete(db, _tenant_id(actor), supervisor_id)


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE PERMISO
# ─────────────────────────────────────────────────────────────────────────────

router_tipos_permiso = APIRouter(prefix="/rrhh/tipos-permiso", tags=["RRHH - Tipos de Permiso"])


@router_tipos_permiso.get("", response_model=TipoPermisoList)
def list_tipos_permiso(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.tipos_permiso.read")),
):
    items, total = TipoPermisoService.list(db, _tenant_id(actor), page, size, solo_activos)
    return TipoPermisoList(items=[TipoPermisoRead.model_validate(i) for i in items],
                           total=total, page=page, size=size)


@router_tipos_permiso.post("", response_model=TipoPermisoRead, status_code=status.HTTP_201_CREATED)
def create_tipo_permiso(
    body: TipoPermisoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.tipos_permiso.create")),
):
    obj = TipoPermisoService.create(db, _tenant_id(actor), body)
    return TipoPermisoRead.model_validate(obj)


@router_tipos_permiso.patch("/{tipo_id}", response_model=TipoPermisoRead)
def update_tipo_permiso(
    tipo_id: UUID,
    body: TipoPermisoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.tipos_permiso.update")),
):
    obj = TipoPermisoService.update(db, _tenant_id(actor), tipo_id, body)
    return TipoPermisoRead.model_validate(obj)


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS EVALUACIONES
# ─────────────────────────────────────────────────────────────────────────────

router_eval = APIRouter(prefix="/rrhh/evaluaciones", tags=["RRHH - Catálogos Evaluaciones"])


@router_eval.get("/cuantitativas", response_model=list[EvaluacionCuantitativaRead])
def list_eval_cuantitativas(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.read")),
):
    return [EvaluacionCuantitativaRead.model_validate(i)
            for i in EvaluacionCuantitativaService.list(db, _tenant_id(actor))]


@router_eval.post("/cuantitativas", response_model=EvaluacionCuantitativaRead,
                  status_code=status.HTTP_201_CREATED)
def create_eval_cuantitativa(
    body: EvaluacionCuantitativaCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.create")),
):
    return EvaluacionCuantitativaRead.model_validate(
        EvaluacionCuantitativaService.create(db, _tenant_id(actor), body)
    )


@router_eval.patch("/cuantitativas/{eval_id}", response_model=EvaluacionCuantitativaRead)
def update_eval_cuantitativa(
    eval_id: UUID, body: EvaluacionCuantitativaUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.update")),
):
    return EvaluacionCuantitativaRead.model_validate(
        EvaluacionCuantitativaService.update(db, _tenant_id(actor), eval_id, body)
    )


@router_eval.get("/cuantitativas/atributos", response_model=list[AtributoEvalCuantitativaRead])
def list_atributos_cuantitativos(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.read")),
):
    return [AtributoEvalCuantitativaRead.model_validate(i)
            for i in AtributoEvalCuantitativaService.list(db, _tenant_id(actor))]


@router_eval.post("/cuantitativas/atributos", response_model=AtributoEvalCuantitativaRead,
                  status_code=status.HTTP_201_CREATED)
def create_atributo_cuantitativo(
    body: AtributoEvalCuantitativaCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.create")),
):
    return AtributoEvalCuantitativaRead.model_validate(
        AtributoEvalCuantitativaService.create(db, _tenant_id(actor), body)
    )


@router_eval.get("/cualitativas", response_model=list[EvaluacionCualitativaRead])
def list_eval_cualitativas(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.read")),
):
    return [EvaluacionCualitativaRead.model_validate(i)
            for i in EvaluacionCualitativaService.list(db, _tenant_id(actor))]


@router_eval.post("/cualitativas", response_model=EvaluacionCualitativaRead,
                  status_code=status.HTTP_201_CREATED)
def create_eval_cualitativa(
    body: EvaluacionCualitativaCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.create")),
):
    return EvaluacionCualitativaRead.model_validate(
        EvaluacionCualitativaService.create(db, _tenant_id(actor), body)
    )


@router_eval.get("/cualitativas/atributos", response_model=list[AtributoEvalCualitativaRead])
def list_atributos_cualitativos(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.read")),
):
    return [AtributoEvalCualitativaRead.model_validate(i)
            for i in AtributoEvalCualitativaService.list(db, _tenant_id(actor))]


@router_eval.post("/cualitativas/atributos", response_model=AtributoEvalCualitativaRead,
                  status_code=status.HTTP_201_CREATED)
def create_atributo_cualitativo(
    body: AtributoEvalCualitativaCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.create")),
):
    return AtributoEvalCualitativaRead.model_validate(
        AtributoEvalCualitativaService.create(db, _tenant_id(actor), body)
    )


# ─────────────────────────────────────────────────────────────────────────────
# TRABAJADORES
# ─────────────────────────────────────────────────────────────────────────────

router_trabajadores = APIRouter(prefix="/rrhh/trabajadores", tags=["RRHH - Trabajadores"])


@router_trabajadores.get("", response_model=TrabajadorList)
def list_trabajadores(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    solo_activos: bool = Query(True),
    sucursal_id: Optional[UUID] = Query(None),
    centro_costo_id: Optional[UUID] = Query(None),
    cargo_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    items, total = TrabajadorService.list(
        db, _tenant_id(actor), page, size, search, solo_activos,
        sucursal_id, centro_costo_id, cargo_id
    )
    return TrabajadorList(
        items=[TrabajadorListItem.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_trabajadores.post("", response_model=TrabajadorRead, status_code=status.HTTP_201_CREATED)
def create_trabajador(
    body: TrabajadorCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.create")),
):
    obj = TrabajadorService.create(db, _tenant_id(actor), body)
    return TrabajadorRead.model_validate(obj)


@router_trabajadores.get("/{trabajador_id}", response_model=TrabajadorRead)
def get_trabajador(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    obj = TrabajadorService.get_or_404(db, _tenant_id(actor), trabajador_id)
    return TrabajadorRead.model_validate(obj)


@router_trabajadores.patch("/{trabajador_id}", response_model=TrabajadorRead)
def update_trabajador(
    trabajador_id: UUID,
    body: TrabajadorUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    obj = TrabajadorService.update(db, _tenant_id(actor), trabajador_id, body)
    return TrabajadorRead.model_validate(obj)


@router_trabajadores.patch("/{trabajador_id}/desactivar", response_model=TrabajadorRead)
def desactivar_trabajador(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.delete")),
):
    obj = TrabajadorService.deactivate(db, _tenant_id(actor), trabajador_id)
    return TrabajadorRead.model_validate(obj)


# ── APV ───────────────────────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/apv", response_model=list[TrabajadorApvRead])
def list_apv(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    return [TrabajadorApvRead.model_validate(i)
            for i in TrabajadorApvService.list(db, _tenant_id(actor), trabajador_id)]


@router_trabajadores.post("/{trabajador_id}/apv", response_model=TrabajadorApvRead,
                          status_code=status.HTTP_201_CREATED)
def create_apv(
    trabajador_id: UUID,
    body: TrabajadorApvCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return TrabajadorApvRead.model_validate(
        TrabajadorApvService.create(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.patch("/{trabajador_id}/apv/{apv_id}", response_model=TrabajadorApvRead)
def update_apv(
    trabajador_id: UUID, apv_id: UUID,
    body: TrabajadorApvUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return TrabajadorApvRead.model_validate(
        TrabajadorApvService.update(db, _tenant_id(actor), apv_id, body)
    )


@router_trabajadores.delete("/{trabajador_id}/apv/{apv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_apv(
    trabajador_id: UUID, apv_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    TrabajadorApvService.delete(db, _tenant_id(actor), apv_id)


# ── CÓNYUGE AFILIADO ──────────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/conyuge", response_model=Optional[ConyugeAfiliadoRead])
def get_conyuge(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    return ConyugeAfiliadoService.get(db, _tenant_id(actor), trabajador_id)


@router_trabajadores.put("/{trabajador_id}/conyuge", response_model=ConyugeAfiliadoRead)
def upsert_conyuge(
    trabajador_id: UUID,
    body: ConyugeAfiliadoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return ConyugeAfiliadoRead.model_validate(
        ConyugeAfiliadoService.upsert(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.delete("/{trabajador_id}/conyuge", status_code=status.HTTP_204_NO_CONTENT)
def delete_conyuge(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    ConyugeAfiliadoService.delete(db, _tenant_id(actor), trabajador_id)


# ── CARGAS FAMILIARES ─────────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/cargas", response_model=CargaFamiliarList)
def list_cargas(
    trabajador_id: UUID,
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    items = CargaFamiliarService.list(db, _tenant_id(actor), trabajador_id, solo_activas)
    return CargaFamiliarList(items=[CargaFamiliarRead.model_validate(i) for i in items],
                             total=len(items))


@router_trabajadores.post("/{trabajador_id}/cargas", response_model=CargaFamiliarRead,
                          status_code=status.HTTP_201_CREATED)
def create_carga(
    trabajador_id: UUID,
    body: CargaFamiliarCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return CargaFamiliarRead.model_validate(
        CargaFamiliarService.create(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.patch("/{trabajador_id}/cargas/{carga_id}", response_model=CargaFamiliarRead)
def update_carga(
    trabajador_id: UUID, carga_id: UUID,
    body: CargaFamiliarUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return CargaFamiliarRead.model_validate(
        CargaFamiliarService.update(db, _tenant_id(actor), carga_id, body)
    )


# ── VACACIONES ────────────────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/vacaciones", response_model=FichaVacacionList)
def list_vacaciones(
    trabajador_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.vacaciones.read")),
):
    items, total = FichaVacacionService.list(db, _tenant_id(actor), trabajador_id, page, size)
    return FichaVacacionList(items=[FichaVacacionRead.model_validate(i) for i in items],
                             total=total)


@router_trabajadores.post("/{trabajador_id}/vacaciones", response_model=FichaVacacionRead,
                          status_code=status.HTTP_201_CREATED)
def create_vacacion(
    trabajador_id: UUID,
    body: FichaVacacionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.vacaciones.create")),
):
    return FichaVacacionRead.model_validate(
        FichaVacacionService.create(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.patch("/{trabajador_id}/vacaciones/{vac_id}", response_model=FichaVacacionRead)
def update_vacacion(
    trabajador_id: UUID, vac_id: UUID,
    body: FichaVacacionUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.vacaciones.update")),
):
    return FichaVacacionRead.model_validate(
        FichaVacacionService.update(db, _tenant_id(actor), vac_id, body)
    )


@router_trabajadores.delete("/{trabajador_id}/vacaciones/{vac_id}",
                            status_code=status.HTTP_204_NO_CONTENT)
def delete_vacacion(
    trabajador_id: UUID, vac_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.vacaciones.delete")),
):
    FichaVacacionService.delete(db, _tenant_id(actor), vac_id)


@router_trabajadores.get("/{trabajador_id}/vacaciones/resumen")
def resumen_vacaciones(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.vacaciones.read")),
):
    return FichaVacacionService.resumen_dias(db, _tenant_id(actor), trabajador_id)


# ── PERMISOS ──────────────────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/permisos", response_model=FichaPermisoList)
def list_permisos(
    trabajador_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.permisos.read")),
):
    items, total = FichaPermisoService.list(db, _tenant_id(actor), trabajador_id, page, size)
    return FichaPermisoList(items=[FichaPermisoRead.model_validate(i) for i in items], total=total)


@router_trabajadores.post("/{trabajador_id}/permisos", response_model=FichaPermisoRead,
                          status_code=status.HTTP_201_CREATED)
def create_permiso(
    trabajador_id: UUID,
    body: FichaPermisoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.permisos.create")),
):
    return FichaPermisoRead.model_validate(
        FichaPermisoService.create(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.patch("/{trabajador_id}/permisos/{permiso_id}", response_model=FichaPermisoRead)
def update_permiso(
    trabajador_id: UUID, permiso_id: UUID,
    body: FichaPermisoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.permisos.update")),
):
    return FichaPermisoRead.model_validate(
        FichaPermisoService.update(db, _tenant_id(actor), permiso_id, body)
    )


@router_trabajadores.delete("/{trabajador_id}/permisos/{permiso_id}",
                            status_code=status.HTTP_204_NO_CONTENT)
def delete_permiso(
    trabajador_id: UUID, permiso_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.permisos.delete")),
):
    FichaPermisoService.delete(db, _tenant_id(actor), permiso_id)


# ── OBSERVACIONES ─────────────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/observaciones", response_model=ObservacionList)
def list_observaciones(
    trabajador_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    items, total = ObservacionService.list(db, _tenant_id(actor), trabajador_id, page, size)
    return ObservacionList(items=[ObservacionRead.model_validate(i) for i in items], total=total)


@router_trabajadores.post("/{trabajador_id}/observaciones", response_model=ObservacionRead,
                          status_code=status.HTTP_201_CREATED)
def create_observacion(
    trabajador_id: UUID,
    body: ObservacionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return ObservacionRead.model_validate(
        ObservacionService.create(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.patch("/{trabajador_id}/observaciones/{obs_id}", response_model=ObservacionRead)
def update_observacion(
    trabajador_id: UUID, obs_id: UUID,
    body: ObservacionUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return ObservacionRead.model_validate(
        ObservacionService.update(db, _tenant_id(actor), obs_id, body)
    )


@router_trabajadores.delete("/{trabajador_id}/observaciones/{obs_id}",
                            status_code=status.HTTP_204_NO_CONTENT)
def delete_observacion(
    trabajador_id: UUID, obs_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    ObservacionService.delete(db, _tenant_id(actor), obs_id)


# ── CARGOS DESEMPEÑADOS ───────────────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/cargos-desempenados",
                         response_model=list[CargoDesempenadoRead])
def list_cargos_desempenados(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.read")),
):
    return [CargoDesempenadoRead.model_validate(i)
            for i in CargoDesempenadoService.list(db, _tenant_id(actor), trabajador_id)]


@router_trabajadores.post("/{trabajador_id}/cargos-desempenados",
                          response_model=CargoDesempenadoRead, status_code=status.HTTP_201_CREATED)
def create_cargo_desempenado(
    trabajador_id: UUID,
    body: CargoDesempenadoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return CargoDesempenadoRead.model_validate(
        CargoDesempenadoService.create(db, _tenant_id(actor), trabajador_id, body)
    )


@router_trabajadores.patch("/{trabajador_id}/cargos-desempenados/{cargo_id}",
                           response_model=CargoDesempenadoRead)
def update_cargo_desempenado(
    trabajador_id: UUID, cargo_id: UUID,
    body: CargoDesempenadoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.trabajadores.update")),
):
    return CargoDesempenadoRead.model_validate(
        CargoDesempenadoService.update(db, _tenant_id(actor), cargo_id, body)
    )


# ── EVALUACIONES DEL TRABAJADOR ───────────────────────────────────────────────

@router_trabajadores.get("/{trabajador_id}/evaluaciones/cuantitativas",
                         response_model=list[TrabajadorEvalCuantitativaRead])
def list_eval_cuantitativas_trabajador(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.read")),
):
    return [TrabajadorEvalCuantitativaRead.model_validate(i)
            for i in TrabajadorEvalService.list_cuantitativas(db, _tenant_id(actor), trabajador_id)]


@router_trabajadores.post("/{trabajador_id}/evaluaciones/cuantitativas",
                          response_model=TrabajadorEvalCuantitativaRead,
                          status_code=status.HTTP_201_CREATED)
def create_eval_cuantitativa_trabajador(
    trabajador_id: UUID,
    body: TrabajadorEvalCuantitativaCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.create")),
):
    return TrabajadorEvalCuantitativaRead.model_validate(
        TrabajadorEvalService.create_cuantitativa(
            db, _tenant_id(actor), trabajador_id, actor.id, body
        )
    )


@router_trabajadores.get("/{trabajador_id}/evaluaciones/cualitativas",
                         response_model=list[TrabajadorEvalCualitativaRead])
def list_eval_cualitativas_trabajador(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.read")),
):
    return [TrabajadorEvalCualitativaRead.model_validate(i)
            for i in TrabajadorEvalService.list_cualitativas(db, _tenant_id(actor), trabajador_id)]


@router_trabajadores.post("/{trabajador_id}/evaluaciones/cualitativas",
                          response_model=TrabajadorEvalCualitativaRead,
                          status_code=status.HTTP_201_CREATED)
def create_eval_cualitativa_trabajador(
    trabajador_id: UUID,
    body: TrabajadorEvalCualitativaCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("rrhh.evaluaciones.create")),
):
    return TrabajadorEvalCualitativaRead.model_validate(
        TrabajadorEvalService.create_cualitativa(
            db, _tenant_id(actor), trabajador_id, actor.id, body
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Router principal del módulo (agrupa todos los sub-routers)
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()
router.include_router(router_supervisores)
router.include_router(router_tipos_permiso)
router.include_router(router_eval)
router.include_router(router_trabajadores)
