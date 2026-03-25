"""
modulos/nomina/endpoints.py
===========================
Rutas FastAPI para el módulo Nómina — Iteración 2.

Catálogos globales: acceso autenticado, sin restricción de tenant.
  - Solo superadmin puede modificar tasas/tramos/factores.
  - Cualquier usuario autenticado puede leer.

Operacionales (tenant-scoped):
  - Requieren permiso específico por recurso.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission, require_superadmin
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import MessageResponse

from modulos.nomina.schemas import (
    AfpRead, AfpUpdate,
    BancoRead, CcafRead,
    CausalFiniquitoCreate, CausalFiniquitoList, CausalFiniquitoRead, CausalFiniquitoUpdate,
    CargoCreate, CargoList, CargoRead, CargoUpdate,
    CentroCostoCreate, CentroCostoList, CentroCostoRead, CentroCostoUpdate,
    ClausulaAdicionalCreate, ClausulaAdicionalList, ClausulaAdicionalRead, ClausulaAdicionalUpdate,
    ComunaRead,
    ConceptoRemuneracionCreate, ConceptoRemuneracionList,
    ConceptoRemuneracionRead, ConceptoRemuneracionUpdate,
    EmpresaConfigCreate, EmpresaConfigRead, EmpresaConfigUpdate,
    FactorActualizacionCreate, FactorActualizacionRead, FactorActualizacionUpdate,
    IsapreRead, IsapreUpdate,
    MutualidadRead,
    ParametroMensualCreate, ParametroMensualList, ParametroMensualRead, ParametroMensualUpdate,
    RegionRead,
    ServMedCchcCreate, ServMedCchcRead, ServMedCchcUpdate,
    SucursalCreate, SucursalList, SucursalRead, SucursalUpdate,
    TipoContratoCreate, TipoContratoList, TipoContratoRead, TipoContratoUpdate,
    TipoMonedaRead, TipoMovimientoBancarioRead,
    TramoAsignacionFamiliarCreate, TramoAsignacionFamiliarRead,
    TramoImpuestoUnicoCreate, TramoImpuestoUnicoRead,
)
from modulos.nomina.services import (
    AfpService, BancoService, CargoService,
    CausalFiniquitoService, CcafService, CentroCostoService,
    ClausulaAdicionalService, ConceptoRemuneracionService,
    ComunaService, EmpresaConfigService, FactorActualizacionService,
    IsapreService, MutualidadService, ParametroMensualService,
    RegionService, ServMedCchcService, SucursalService,
    TipoContratoService, TipoMonedaService,
    TramoAsignacionFamiliarService, TramoImpuestoUnicoService,
)


def _tenant_id(actor: User) -> UUID:
    return actor.tenant_id


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS GLOBALES — AFP
# ─────────────────────────────────────────────────────────────────────────────

router_afp = APIRouter(prefix="/nomina/catalogos/afp", tags=["Nómina - AFP"])


@router_afp.get("", response_model=list[AfpRead])
def list_afp(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [AfpRead.model_validate(i) for i in AfpService.list(db, solo_activas)]


@router_afp.get("/{afp_id}", response_model=AfpRead)
def get_afp(
    afp_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return AfpRead.model_validate(AfpService.get_or_404(db, afp_id))


@router_afp.patch("/{afp_id}", response_model=AfpRead)
def update_afp(
    afp_id: int,
    body: AfpUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Solo superadmin puede actualizar tasas AFP."""
    return AfpRead.model_validate(AfpService.update(db, afp_id, body))


# ─────────────────────────────────────────────────────────────────────────────
# ISAPRES
# ─────────────────────────────────────────────────────────────────────────────

router_isapre = APIRouter(prefix="/nomina/catalogos/isapres", tags=["Nómina - Isapres"])


@router_isapre.get("", response_model=list[IsapreRead])
def list_isapres(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [IsapreRead.model_validate(i) for i in IsapreService.list(db, solo_activas)]


@router_isapre.get("/{isapre_id}", response_model=IsapreRead)
def get_isapre(
    isapre_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return IsapreRead.model_validate(IsapreService.get_or_404(db, isapre_id))


@router_isapre.patch("/{isapre_id}", response_model=IsapreRead)
def update_isapre(
    isapre_id: int,
    body: IsapreUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return IsapreRead.model_validate(IsapreService.update(db, isapre_id, body))


# ─────────────────────────────────────────────────────────────────────────────
# CCAF
# ─────────────────────────────────────────────────────────────────────────────

router_ccaf = APIRouter(prefix="/nomina/catalogos/ccaf", tags=["Nómina - CCAF"])


@router_ccaf.get("", response_model=list[CcafRead])
def list_ccaf(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [CcafRead.model_validate(i) for i in CcafService.list(db, solo_activas)]


@router_ccaf.get("/{ccaf_id}", response_model=CcafRead)
def get_ccaf(
    ccaf_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return CcafRead.model_validate(CcafService.get_or_404(db, ccaf_id))


# ─────────────────────────────────────────────────────────────────────────────
# MUTUALIDADES
# ─────────────────────────────────────────────────────────────────────────────

router_mutualidad = APIRouter(prefix="/nomina/catalogos/mutualidades",
                              tags=["Nómina - Mutualidades"])


@router_mutualidad.get("", response_model=list[MutualidadRead])
def list_mutualidades(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [MutualidadRead.model_validate(i) for i in MutualidadService.list(db, solo_activas)]


@router_mutualidad.get("/{mut_id}", response_model=MutualidadRead)
def get_mutualidad(
    mut_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return MutualidadRead.model_validate(MutualidadService.get_or_404(db, mut_id))


# ─────────────────────────────────────────────────────────────────────────────
# BANCOS
# ─────────────────────────────────────────────────────────────────────────────

router_banco = APIRouter(prefix="/nomina/catalogos/bancos", tags=["Nómina - Bancos"])


@router_banco.get("", response_model=list[BancoRead])
def list_bancos(
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [BancoRead.model_validate(i) for i in BancoService.list(db, solo_activos)]


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS MOVIMIENTO BANCARIO
# ─────────────────────────────────────────────────────────────────────────────

router_mov_bancario = APIRouter(prefix="/nomina/catalogos/movimientos-bancarios",
                                tags=["Nómina - Movimientos Bancarios"])


@router_mov_bancario.get("", response_model=list[TipoMovimientoBancarioRead])
def list_movimientos_bancarios(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from modulos.nomina.repositories import TipoMovimientoBancarioRepository
    return [TipoMovimientoBancarioRead.model_validate(i)
            for i in TipoMovimientoBancarioRepository.get_all(db)]


# ─────────────────────────────────────────────────────────────────────────────
# REGIONES Y COMUNAS
# ─────────────────────────────────────────────────────────────────────────────

router_geo = APIRouter(prefix="/nomina/catalogos", tags=["Nómina - Geografía"])


@router_geo.get("/regiones", response_model=list[RegionRead])
def list_regiones(
    solo_zona_extrema: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [RegionRead.model_validate(i)
            for i in RegionService.list(db, solo_zona_extrema)]


@router_geo.get("/regiones/{region_id}/comunas", response_model=list[ComunaRead])
def list_comunas_por_region(
    region_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    RegionService.get_or_404(db, region_id)
    return [ComunaRead.model_validate(i) for i in ComunaService.list(db, region_id)]


@router_geo.get("/comunas", response_model=list[ComunaRead])
def list_comunas(
    region_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [ComunaRead.model_validate(i) for i in ComunaService.list(db, region_id)]


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE MONEDA
# ─────────────────────────────────────────────────────────────────────────────

router_moneda = APIRouter(prefix="/nomina/catalogos/monedas", tags=["Nómina - Monedas"])


@router_moneda.get("", response_model=list[TipoMonedaRead])
def list_monedas(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [TipoMonedaRead.model_validate(i) for i in TipoMonedaService.list(db, solo_activas)]


# ─────────────────────────────────────────────────────────────────────────────
# TRAMOS ASIGNACIÓN FAMILIAR
# ─────────────────────────────────────────────────────────────────────────────

router_af = APIRouter(prefix="/nomina/parametros/asignacion-familiar",
                      tags=["Nómina - Asignación Familiar"])


@router_af.get("/vigente", response_model=list[TramoAsignacionFamiliarRead])
def get_tramos_af_vigentes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [TramoAsignacionFamiliarRead.model_validate(i)
            for i in TramoAsignacionFamiliarService.get_vigente(db)]


@router_af.get("/{anio}/{mes}", response_model=list[TramoAsignacionFamiliarRead])
def get_tramos_af_periodo(
    anio: int, mes: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [TramoAsignacionFamiliarRead.model_validate(i)
            for i in TramoAsignacionFamiliarService.get_por_periodo(db, anio, mes)]


@router_af.put("/{anio}/{mes}", response_model=list[TramoAsignacionFamiliarRead])
def reemplazar_tramos_af(
    anio: int, mes: int,
    tramos: list[TramoAsignacionFamiliarCreate],
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Reemplaza todos los tramos de un período. Superadmin only."""
    result = TramoAsignacionFamiliarService.reemplazar_periodo(db, anio, mes, tramos)
    return [TramoAsignacionFamiliarRead.model_validate(i) for i in result]


# ─────────────────────────────────────────────────────────────────────────────
# TRAMOS IMPUESTO ÚNICO
# ─────────────────────────────────────────────────────────────────────────────

router_iu = APIRouter(prefix="/nomina/parametros/impuesto-unico",
                      tags=["Nómina - Impuesto Único"])


@router_iu.get("/vigente", response_model=list[TramoImpuestoUnicoRead])
def get_tramos_iu_vigentes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [TramoImpuestoUnicoRead.model_validate(i)
            for i in TramoImpuestoUnicoService.get_vigente(db)]


@router_iu.get("/{anio}/{mes}", response_model=list[TramoImpuestoUnicoRead])
def get_tramos_iu_periodo(
    anio: int, mes: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [TramoImpuestoUnicoRead.model_validate(i)
            for i in TramoImpuestoUnicoService.get_por_periodo(db, anio, mes)]


@router_iu.put("/{anio}/{mes}", response_model=list[TramoImpuestoUnicoRead])
def reemplazar_tramos_iu(
    anio: int, mes: int,
    tramos: list[TramoImpuestoUnicoCreate],
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Reemplaza todos los tramos de un período. Superadmin only."""
    result = TramoImpuestoUnicoService.reemplazar_periodo(db, anio, mes, tramos)
    return [TramoImpuestoUnicoRead.model_validate(i) for i in result]


# ─────────────────────────────────────────────────────────────────────────────
# FACTORES UTM / UF / IMM
# ─────────────────────────────────────────────────────────────────────────────

router_factor = APIRouter(prefix="/nomina/parametros/factores",
                          tags=["Nómina - Factores UTM/UF/IMM"])


@router_factor.get("", response_model=list[FactorActualizacionRead])
def list_factores(
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [FactorActualizacionRead.model_validate(i)
            for i in FactorActualizacionService.list(db, anio)]


@router_factor.get("/vigente", response_model=FactorActualizacionRead)
def get_factor_vigente(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = FactorActualizacionService.get_vigente(db)
    if not obj:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No hay factores cargados.")
    return FactorActualizacionRead.model_validate(obj)


@router_factor.post("", response_model=FactorActualizacionRead,
                    status_code=status.HTTP_201_CREATED)
def create_factor(
    body: FactorActualizacionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return FactorActualizacionRead.model_validate(FactorActualizacionService.create(db, body))


@router_factor.patch("/{anio}/{mes}", response_model=FactorActualizacionRead)
def update_factor(
    anio: int, mes: int,
    body: FactorActualizacionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return FactorActualizacionRead.model_validate(
        FactorActualizacionService.update(db, anio, mes, body)
    )


# ─────────────────────────────────────────────────────────────────────────────
# SERVICIO MÉDICO CCHC
# ─────────────────────────────────────────────────────────────────────────────

router_cchc = APIRouter(prefix="/nomina/parametros/serv-med-cchc",
                        tags=["Nómina - Serv. Méd. CCHC"])


@router_cchc.get("/vigente", response_model=ServMedCchcRead)
def get_serv_med_vigente(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = ServMedCchcService.get_vigente(db)
    if not obj:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No hay parámetros CCHC cargados.")
    return ServMedCchcRead.model_validate(obj)


@router_cchc.post("", response_model=ServMedCchcRead, status_code=status.HTTP_201_CREATED)
def create_serv_med(
    body: ServMedCchcCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return ServMedCchcRead.model_validate(ServMedCchcService.create(db, body))


@router_cchc.patch("/{anio}/{mes}", response_model=ServMedCchcRead)
def update_serv_med(
    anio: int, mes: int,
    body: ServMedCchcUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return ServMedCchcRead.model_validate(ServMedCchcService.update(db, anio, mes, body))


# ─────────────────────────────────────────────────────────────────────────────
# EMPRESA CONFIG (tenant-scoped)
# ─────────────────────────────────────────────────────────────────────────────

router_empresa = APIRouter(prefix="/nomina/empresa", tags=["Nómina - Configuración Empresa"])


@router_empresa.get("", response_model=EmpresaConfigRead)
def get_empresa_config(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.empresa.read")),
):
    return EmpresaConfigRead.model_validate(
        EmpresaConfigService.get_or_404(db, _tenant_id(actor))
    )


@router_empresa.put("", response_model=EmpresaConfigRead)
def upsert_empresa_config(
    body: EmpresaConfigCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.empresa.update")),
):
    return EmpresaConfigRead.model_validate(
        EmpresaConfigService.upsert(db, _tenant_id(actor), body)
    )


@router_empresa.patch("", response_model=EmpresaConfigRead)
def update_empresa_config(
    body: EmpresaConfigUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.empresa.update")),
):
    return EmpresaConfigRead.model_validate(
        EmpresaConfigService.update(db, _tenant_id(actor), body)
    )


# ─────────────────────────────────────────────────────────────────────────────
# SUCURSALES
# ─────────────────────────────────────────────────────────────────────────────

router_sucursal = APIRouter(prefix="/nomina/sucursales", tags=["Nómina - Sucursales"])


@router_sucursal.get("", response_model=SucursalList)
def list_sucursales(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.sucursales.read")),
):
    items, total = SucursalService.list(db, _tenant_id(actor), page, size, solo_activas)
    return SucursalList(items=[SucursalRead.model_validate(i) for i in items],
                        total=total, page=page, size=size)


@router_sucursal.post("", response_model=SucursalRead, status_code=status.HTTP_201_CREATED)
def create_sucursal(
    body: SucursalCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.sucursales.create")),
):
    return SucursalRead.model_validate(SucursalService.create(db, _tenant_id(actor), body))


@router_sucursal.get("/{sucursal_id}", response_model=SucursalRead)
def get_sucursal(
    sucursal_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.sucursales.read")),
):
    return SucursalRead.model_validate(
        SucursalService.get_or_404(db, _tenant_id(actor), sucursal_id)
    )


@router_sucursal.patch("/{sucursal_id}", response_model=SucursalRead)
def update_sucursal(
    sucursal_id: UUID,
    body: SucursalUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.sucursales.update")),
):
    return SucursalRead.model_validate(
        SucursalService.update(db, _tenant_id(actor), sucursal_id, body)
    )


@router_sucursal.delete("/{sucursal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sucursal(
    sucursal_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.sucursales.delete")),
):
    SucursalService.delete(db, _tenant_id(actor), sucursal_id)


# ─────────────────────────────────────────────────────────────────────────────
# CENTROS DE COSTO
# ─────────────────────────────────────────────────────────────────────────────

router_cc = APIRouter(prefix="/nomina/centros-costo", tags=["Nómina - Centros de Costo"])


@router_cc.get("", response_model=CentroCostoList)
def list_centros_costo(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.centros_costo.read")),
):
    items, total = CentroCostoService.list(db, _tenant_id(actor), page, size, solo_activos)
    return CentroCostoList(items=[CentroCostoRead.model_validate(i) for i in items],
                           total=total, page=page, size=size)


@router_cc.post("", response_model=CentroCostoRead, status_code=status.HTTP_201_CREATED)
def create_centro_costo(
    body: CentroCostoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.centros_costo.create")),
):
    return CentroCostoRead.model_validate(CentroCostoService.create(db, _tenant_id(actor), body))


@router_cc.get("/{cc_id}", response_model=CentroCostoRead)
def get_centro_costo(
    cc_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.centros_costo.read")),
):
    return CentroCostoRead.model_validate(
        CentroCostoService.get_or_404(db, _tenant_id(actor), cc_id)
    )


@router_cc.patch("/{cc_id}", response_model=CentroCostoRead)
def update_centro_costo(
    cc_id: UUID,
    body: CentroCostoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.centros_costo.update")),
):
    return CentroCostoRead.model_validate(
        CentroCostoService.update(db, _tenant_id(actor), cc_id, body)
    )


@router_cc.delete("/{cc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_centro_costo(
    cc_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.centros_costo.delete")),
):
    CentroCostoService.delete(db, _tenant_id(actor), cc_id)


# ─────────────────────────────────────────────────────────────────────────────
# CARGOS
# ─────────────────────────────────────────────────────────────────────────────

router_cargo = APIRouter(prefix="/nomina/cargos", tags=["Nómina - Cargos"])


@router_cargo.get("", response_model=CargoList)
def list_cargos(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    search: str = Query(""),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.cargos.read")),
):
    items, total = CargoService.list(db, _tenant_id(actor), page, size, search, solo_activos)
    return CargoList(items=[CargoRead.model_validate(i) for i in items],
                     total=total, page=page, size=size)


@router_cargo.post("", response_model=CargoRead, status_code=status.HTTP_201_CREATED)
def create_cargo(
    body: CargoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.cargos.create")),
):
    return CargoRead.model_validate(CargoService.create(db, _tenant_id(actor), body))


@router_cargo.get("/{cargo_id}", response_model=CargoRead)
def get_cargo(
    cargo_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.cargos.read")),
):
    return CargoRead.model_validate(CargoService.get_or_404(db, _tenant_id(actor), cargo_id))


@router_cargo.patch("/{cargo_id}", response_model=CargoRead)
def update_cargo(
    cargo_id: UUID,
    body: CargoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.cargos.update")),
):
    return CargoRead.model_validate(CargoService.update(db, _tenant_id(actor), cargo_id, body))


@router_cargo.delete("/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cargo(
    cargo_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.cargos.delete")),
):
    CargoService.delete(db, _tenant_id(actor), cargo_id)


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE CONTRATO
# ─────────────────────────────────────────────────────────────────────────────

router_tipo_contrato = APIRouter(prefix="/nomina/tipos-contrato",
                                 tags=["Nómina - Tipos de Contrato"])


@router_tipo_contrato.get("", response_model=TipoContratoList)
def list_tipos_contrato(
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.tipos_contrato.read")),
):
    items = TipoContratoService.list(db, _tenant_id(actor), solo_activos)
    return TipoContratoList(items=[TipoContratoRead.model_validate(i) for i in items],
                            total=len(items), page=1, size=len(items))


@router_tipo_contrato.post("", response_model=TipoContratoRead,
                           status_code=status.HTTP_201_CREATED)
def create_tipo_contrato(
    body: TipoContratoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.tipos_contrato.create")),
):
    return TipoContratoRead.model_validate(
        TipoContratoService.create(db, _tenant_id(actor), body)
    )


@router_tipo_contrato.patch("/{tc_id}", response_model=TipoContratoRead)
def update_tipo_contrato(
    tc_id: UUID,
    body: TipoContratoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.tipos_contrato.update")),
):
    return TipoContratoRead.model_validate(
        TipoContratoService.update(db, _tenant_id(actor), tc_id, body)
    )


@router_tipo_contrato.delete("/{tc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_contrato(
    tc_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.tipos_contrato.delete")),
):
    TipoContratoService.delete(db, _tenant_id(actor), tc_id)


# ─────────────────────────────────────────────────────────────────────────────
# CAUSALES DE FINIQUITO
# ─────────────────────────────────────────────────────────────────────────────

router_causal = APIRouter(prefix="/nomina/causales-finiquito",
                          tags=["Nómina - Causales de Finiquito"])


@router_causal.get("", response_model=CausalFiniquitoList)
def list_causales(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.causales_finiquito.read")),
):
    items = CausalFiniquitoService.list(db, _tenant_id(actor), solo_activas)
    return CausalFiniquitoList(items=[CausalFiniquitoRead.model_validate(i) for i in items],
                               total=len(items))


@router_causal.post("", response_model=CausalFiniquitoRead,
                    status_code=status.HTTP_201_CREATED)
def create_causal(
    body: CausalFiniquitoCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.causales_finiquito.create")),
):
    return CausalFiniquitoRead.model_validate(
        CausalFiniquitoService.create(db, _tenant_id(actor), body)
    )


@router_causal.patch("/{causal_id}", response_model=CausalFiniquitoRead)
def update_causal(
    causal_id: UUID,
    body: CausalFiniquitoUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.causales_finiquito.update")),
):
    return CausalFiniquitoRead.model_validate(
        CausalFiniquitoService.update(db, _tenant_id(actor), causal_id, body)
    )


@router_causal.delete("/{causal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_causal(
    causal_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.causales_finiquito.delete")),
):
    CausalFiniquitoService.delete(db, _tenant_id(actor), causal_id)


# ─────────────────────────────────────────────────────────────────────────────
# CLÁUSULAS ADICIONALES
# ─────────────────────────────────────────────────────────────────────────────

router_clausula = APIRouter(prefix="/nomina/clausulas-adicionales",
                            tags=["Nómina - Cláusulas Adicionales"])


@router_clausula.get("", response_model=ClausulaAdicionalList)
def list_clausulas(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.clausulas.read")),
):
    items = ClausulaAdicionalService.list(db, _tenant_id(actor), solo_activas)
    return ClausulaAdicionalList(items=[ClausulaAdicionalRead.model_validate(i) for i in items],
                                 total=len(items))


@router_clausula.post("", response_model=ClausulaAdicionalRead,
                      status_code=status.HTTP_201_CREATED)
def create_clausula(
    body: ClausulaAdicionalCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.clausulas.create")),
):
    return ClausulaAdicionalRead.model_validate(
        ClausulaAdicionalService.create(db, _tenant_id(actor), body)
    )


@router_clausula.patch("/{clausula_id}", response_model=ClausulaAdicionalRead)
def update_clausula(
    clausula_id: UUID,
    body: ClausulaAdicionalUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.clausulas.update")),
):
    return ClausulaAdicionalRead.model_validate(
        ClausulaAdicionalService.update(db, _tenant_id(actor), clausula_id, body)
    )


@router_clausula.delete("/{clausula_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clausula(
    clausula_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.clausulas.delete")),
):
    ClausulaAdicionalService.delete(db, _tenant_id(actor), clausula_id)


# ─────────────────────────────────────────────────────────────────────────────
# CONCEPTOS DE REMUNERACIÓN (Haberes y Descuentos)
# ─────────────────────────────────────────────────────────────────────────────

router_concepto = APIRouter(prefix="/nomina/conceptos", tags=["Nómina - Haberes y Descuentos"])


@router_concepto.get("", response_model=ConceptoRemuneracionList)
def list_conceptos(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    tipo: Optional[str] = Query(None, pattern=r"^[HD]$"),
    search: str = Query(""),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.conceptos.read")),
):
    items, total = ConceptoRemuneracionService.list(
        db, _tenant_id(actor), page, size, tipo, search, solo_activos
    )
    return ConceptoRemuneracionList(
        items=[ConceptoRemuneracionRead.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_concepto.post("", response_model=ConceptoRemuneracionRead,
                      status_code=status.HTTP_201_CREATED)
def create_concepto(
    body: ConceptoRemuneracionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.conceptos.create")),
):
    return ConceptoRemuneracionRead.model_validate(
        ConceptoRemuneracionService.create(db, _tenant_id(actor), body)
    )


@router_concepto.get("/{concepto_id}", response_model=ConceptoRemuneracionRead)
def get_concepto(
    concepto_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.conceptos.read")),
):
    return ConceptoRemuneracionRead.model_validate(
        ConceptoRemuneracionService.get_or_404(db, _tenant_id(actor), concepto_id)
    )


@router_concepto.patch("/{concepto_id}", response_model=ConceptoRemuneracionRead)
def update_concepto(
    concepto_id: UUID,
    body: ConceptoRemuneracionUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.conceptos.update")),
):
    return ConceptoRemuneracionRead.model_validate(
        ConceptoRemuneracionService.update(db, _tenant_id(actor), concepto_id, body)
    )


@router_concepto.delete("/{concepto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concepto(
    concepto_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.conceptos.delete")),
):
    ConceptoRemuneracionService.delete(db, _tenant_id(actor), concepto_id)


# ─────────────────────────────────────────────────────────────────────────────
# PARÁMETROS MENSUALES
# ─────────────────────────────────────────────────────────────────────────────

router_parametro = APIRouter(prefix="/nomina/parametros-mensuales",
                             tags=["Nómina - Parámetros Mensuales"])


@router_parametro.get("", response_model=ParametroMensualList)
def list_parametros(
    anio: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.parametros.read")),
):
    items, total = ParametroMensualService.list(db, _tenant_id(actor), anio, page, size)
    return ParametroMensualList(
        items=[ParametroMensualRead.model_validate(i) for i in items],
        total=total, page=page, size=size
    )


@router_parametro.get("/vigente", response_model=ParametroMensualRead)
def get_parametro_vigente(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.parametros.read")),
):
    return ParametroMensualRead.model_validate(
        ParametroMensualService.get_vigente(db, _tenant_id(actor))
    )


@router_parametro.post("", response_model=ParametroMensualRead,
                       status_code=status.HTTP_201_CREATED)
def create_parametro(
    body: ParametroMensualCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.parametros.create")),
):
    return ParametroMensualRead.model_validate(
        ParametroMensualService.create(db, _tenant_id(actor), body)
    )


@router_parametro.get("/{anio}/{mes}", response_model=ParametroMensualRead)
def get_parametro_periodo(
    anio: int, mes: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.parametros.read")),
):
    return ParametroMensualRead.model_validate(
        ParametroMensualService.get_or_404(db, _tenant_id(actor), anio, mes)
    )


@router_parametro.patch("/{anio}/{mes}", response_model=ParametroMensualRead)
def update_parametro(
    anio: int, mes: int,
    body: ParametroMensualUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("nomina.parametros.update")),
):
    return ParametroMensualRead.model_validate(
        ParametroMensualService.update(db, _tenant_id(actor), anio, mes, body)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Router principal del módulo Nómina
# ─────────────────────────────────────────────────────────────────────────────

# Importar router operacional (Iteración 3)
from modulos.nomina.endpoints_operacional import router as router_operacional

# Importar router de cálculo (Iteración 4)
from modulos.nomina.calculo.endpoints_calculo import router as router_calculo

router = APIRouter()
router.include_router(router_afp)
router.include_router(router_isapre)
router.include_router(router_ccaf)
router.include_router(router_mutualidad)
router.include_router(router_banco)
router.include_router(router_mov_bancario)
router.include_router(router_geo)
router.include_router(router_moneda)
router.include_router(router_af)
router.include_router(router_iu)
router.include_router(router_factor)
router.include_router(router_cchc)
router.include_router(router_empresa)
router.include_router(router_sucursal)
router.include_router(router_cc)
router.include_router(router_cargo)
router.include_router(router_tipo_contrato)
router.include_router(router_causal)
router.include_router(router_clausula)
router.include_router(router_concepto)
router.include_router(router_parametro)
router.include_router(router_operacional)  # Iteración 3
router.include_router(router_calculo)      # Iteración 4
