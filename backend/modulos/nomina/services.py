"""
modulos/nomina/services.py
==========================
Lógica de negocio para Nómina.
Catálogos: acceso libre (autenticado). Operacionales: tenant-scoped.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from modulos.nomina.repositories import (
    AfpRepository, BancoRepository, CargoRepository,
    CausalFiniquitoRepository, CcafRepository, CentroCostoRepository,
    ClausulaAdicionalRepository, ConceptoRemuneracionRepository,
    EmpresaConfigRepository, FactorActualizacionRepository,
    IsapreRepository, MutualidadRepository, ParametroMensualRepository,
    RegionRepository, ComunaRepository, ServMedCchcRepository,
    SucursalRepository, TipoContratoRepository, TipoMonedaRepository,
    TipoMovimientoBancarioRepository, TramoAsignacionFamiliarRepository,
    TramoImpuestoUnicoRepository,
)
from modulos.nomina.schemas import (
    AfpUpdate, CausalFiniquitoCreate, CausalFiniquitoUpdate,
    CargoCreate, CargoUpdate, CentroCostoCreate, CentroCostoUpdate,
    ClausulaAdicionalCreate, ClausulaAdicionalUpdate,
    ConceptoRemuneracionCreate, ConceptoRemuneracionUpdate,
    EmpresaConfigCreate, EmpresaConfigUpdate,
    FactorActualizacionCreate, FactorActualizacionUpdate,
    IsapreUpdate, ParametroMensualCreate, ParametroMensualUpdate,
    ServMedCchcCreate, ServMedCchcUpdate,
    SucursalCreate, SucursalUpdate,
    TipoContratoCreate, TipoContratoUpdate,
    TramoAsignacionFamiliarCreate, TramoImpuestoUnicoCreate,
)


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS GLOBALES
# ─────────────────────────────────────────────────────────────────────────────

class AfpService:

    @staticmethod
    def list(db: Session, solo_activas: bool = True):
        return AfpRepository.get_all(db, solo_activas)

    @staticmethod
    def get_or_404(db: Session, afp_id: int):
        obj = AfpRepository.get_by_id(db, afp_id)
        if not obj:
            raise HTTPException(status_code=404, detail="AFP no encontrada.")
        return obj

    @staticmethod
    def update(db: Session, afp_id: int, body: AfpUpdate):
        obj = AfpService.get_or_404(db, afp_id)
        updated = AfpRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class IsapreService:

    @staticmethod
    def list(db: Session, solo_activas: bool = True):
        return IsapreRepository.get_all(db, solo_activas)

    @staticmethod
    def get_or_404(db: Session, isapre_id: int):
        obj = IsapreRepository.get_by_id(db, isapre_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Isapre no encontrada.")
        return obj

    @staticmethod
    def update(db: Session, isapre_id: int, body: IsapreUpdate):
        obj = IsapreService.get_or_404(db, isapre_id)
        updated = IsapreRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class CcafService:

    @staticmethod
    def list(db: Session, solo_activas: bool = True):
        return CcafRepository.get_all(db, solo_activas)

    @staticmethod
    def get_or_404(db: Session, ccaf_id: int):
        obj = CcafRepository.get_by_id(db, ccaf_id)
        if not obj:
            raise HTTPException(status_code=404, detail="CCAF no encontrada.")
        return obj


class MutualidadService:

    @staticmethod
    def list(db: Session, solo_activas: bool = True):
        return MutualidadRepository.get_all(db, solo_activas)

    @staticmethod
    def get_or_404(db: Session, mut_id: int):
        obj = MutualidadRepository.get_by_id(db, mut_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Mutualidad no encontrada.")
        return obj


class BancoService:

    @staticmethod
    def list(db: Session, solo_activos: bool = True):
        return BancoRepository.get_all(db, solo_activos)


class RegionService:

    @staticmethod
    def list(db: Session, solo_zona_extrema: bool = False):
        return RegionRepository.get_all(db, solo_zona_extrema)

    @staticmethod
    def get_or_404(db: Session, region_id: int):
        obj = RegionRepository.get_by_id(db, region_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Región no encontrada.")
        return obj


class ComunaService:

    @staticmethod
    def list(db: Session, region_id: Optional[int] = None):
        return ComunaRepository.get_all(db, region_id)


class TipoMonedaService:

    @staticmethod
    def list(db: Session, solo_activas: bool = True):
        return TipoMonedaRepository.get_all(db, solo_activas)


class TramoAsignacionFamiliarService:

    @staticmethod
    def get_por_periodo(db: Session, anio: int, mes: int):
        return TramoAsignacionFamiliarRepository.get_by_periodo(db, anio, mes)

    @staticmethod
    def get_vigente(db: Session):
        return TramoAsignacionFamiliarRepository.get_ultimo_periodo(db)

    @staticmethod
    def reemplazar_periodo(db: Session, anio: int, mes: int,
                           tramos: list[TramoAsignacionFamiliarCreate]):
        """Reemplaza todos los tramos de un período. Operación atómica."""
        TramoAsignacionFamiliarRepository.delete_periodo(db, anio, mes)
        resultado = []
        for t in tramos:
            obj = TramoAsignacionFamiliarRepository.create(db, t.model_dump())
            resultado.append(obj)
        db.commit()
        return resultado


class TramoImpuestoUnicoService:

    @staticmethod
    def get_por_periodo(db: Session, anio: int, mes: int):
        return TramoImpuestoUnicoRepository.get_by_periodo(db, anio, mes)

    @staticmethod
    def get_vigente(db: Session):
        return TramoImpuestoUnicoRepository.get_ultimo_periodo(db)

    @staticmethod
    def reemplazar_periodo(db: Session, anio: int, mes: int,
                           tramos: list[TramoImpuestoUnicoCreate]):
        """Reemplaza todos los tramos de un período. Operación atómica."""
        TramoImpuestoUnicoRepository.delete_periodo(db, anio, mes)
        resultado = []
        for t in tramos:
            obj = TramoImpuestoUnicoRepository.create(db, t.model_dump())
            resultado.append(obj)
        db.commit()
        return resultado


class FactorActualizacionService:

    @staticmethod
    def list(db: Session, anio: Optional[int] = None):
        return FactorActualizacionRepository.get_all(db, anio)

    @staticmethod
    def get_vigente(db: Session):
        return FactorActualizacionRepository.get_vigente(db)

    @staticmethod
    def get_or_404(db: Session, anio: int, mes: int):
        obj = FactorActualizacionRepository.get_by_periodo(db, anio, mes)
        if not obj:
            raise HTTPException(status_code=404,
                                detail=f"Factor no encontrado para {anio}/{mes:02d}.")
        return obj

    @staticmethod
    def create(db: Session, body: FactorActualizacionCreate):
        if FactorActualizacionRepository.get_by_periodo(db, body.anio, body.mes):
            raise HTTPException(status_code=400,
                                detail=f"Ya existe factor para {body.anio}/{body.mes:02d}.")
        obj = FactorActualizacionRepository.create(db, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, anio: int, mes: int, body: FactorActualizacionUpdate):
        obj = FactorActualizacionService.get_or_404(db, anio, mes)
        updated = FactorActualizacionRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class ServMedCchcService:

    @staticmethod
    def get_vigente(db: Session):
        return ServMedCchcRepository.get_vigente(db)

    @staticmethod
    def get_or_404(db: Session, anio: int, mes: int):
        obj = ServMedCchcRepository.get_by_periodo(db, anio, mes)
        if not obj:
            raise HTTPException(status_code=404,
                                detail=f"Parámetros CCHC no encontrados para {anio}/{mes:02d}.")
        return obj

    @staticmethod
    def create(db: Session, body: ServMedCchcCreate):
        if ServMedCchcRepository.get_by_periodo(db, body.anio, body.mes):
            raise HTTPException(status_code=400,
                                detail=f"Ya existen parámetros CCHC para {body.anio}/{body.mes:02d}.")
        obj = ServMedCchcRepository.create(db, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, anio: int, mes: int, body: ServMedCchcUpdate):
        obj = ServMedCchcService.get_or_404(db, anio, mes)
        updated = ServMedCchcRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


# ─────────────────────────────────────────────────────────────────────────────
# OPERACIONALES (tenant-scoped)
# ─────────────────────────────────────────────────────────────────────────────

class EmpresaConfigService:

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID):
        obj = EmpresaConfigRepository.get(db, tenant_id)
        if not obj:
            raise HTTPException(status_code=404,
                                detail="Configuración de empresa no encontrada.")
        return obj

    @staticmethod
    def upsert(db: Session, tenant_id: UUID, body: EmpresaConfigCreate):
        existing = EmpresaConfigRepository.get(db, tenant_id)
        if existing:
            updated = EmpresaConfigRepository.update(db, existing, body.model_dump())
            db.commit()
            db.refresh(updated)
            return updated
        obj = EmpresaConfigRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, body: EmpresaConfigUpdate):
        obj = EmpresaConfigService.get_or_404(db, tenant_id)
        updated = EmpresaConfigRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated


class SucursalService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int, solo_activas: bool):
        return SucursalRepository.get_all(db, tenant_id, page, size, solo_activas)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, sucursal_id: UUID):
        obj = SucursalRepository.get_by_id(db, tenant_id, sucursal_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: SucursalCreate):
        if SucursalRepository.get_by_codigo(db, tenant_id, body.codigo):
            raise HTTPException(status_code=400,
                                detail=f"Ya existe una sucursal con código '{body.codigo}'.")
        obj = SucursalRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, sucursal_id: UUID, body: SucursalUpdate):
        obj = SucursalService.get_or_404(db, tenant_id, sucursal_id)
        updated = SucursalRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, sucursal_id: UUID):
        obj = SucursalService.get_or_404(db, tenant_id, sucursal_id)
        SucursalRepository.delete(db, obj)
        db.commit()


class CentroCostoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int, solo_activos: bool):
        return CentroCostoRepository.get_all(db, tenant_id, page, size, solo_activos)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, cc_id: UUID):
        obj = CentroCostoRepository.get_by_id(db, tenant_id, cc_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Centro de costo no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: CentroCostoCreate):
        if CentroCostoRepository.get_by_codigo(db, tenant_id, body.codigo):
            raise HTTPException(status_code=400,
                                detail=f"Ya existe un centro de costo con código '{body.codigo}'.")
        obj = CentroCostoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, cc_id: UUID, body: CentroCostoUpdate):
        obj = CentroCostoService.get_or_404(db, tenant_id, cc_id)
        updated = CentroCostoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, cc_id: UUID):
        obj = CentroCostoService.get_or_404(db, tenant_id, cc_id)
        CentroCostoRepository.delete(db, obj)
        db.commit()


class CargoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             search: str, solo_activos: bool):
        return CargoRepository.get_all(db, tenant_id, page, size, search, solo_activos)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, cargo_id: UUID):
        obj = CargoRepository.get_by_id(db, tenant_id, cargo_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Cargo no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: CargoCreate):
        if CargoRepository.get_by_codigo(db, tenant_id, body.codigo):
            raise HTTPException(status_code=400,
                                detail=f"Ya existe un cargo con código '{body.codigo}'.")
        obj = CargoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, cargo_id: UUID, body: CargoUpdate):
        obj = CargoService.get_or_404(db, tenant_id, cargo_id)
        updated = CargoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, cargo_id: UUID):
        obj = CargoService.get_or_404(db, tenant_id, cargo_id)
        CargoRepository.delete(db, obj)
        db.commit()


class TipoContratoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, solo_activos: bool):
        return TipoContratoRepository.get_all(db, tenant_id, solo_activos)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, tc_id: UUID):
        obj = TipoContratoRepository.get_by_id(db, tenant_id, tc_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Tipo de contrato no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: TipoContratoCreate):
        obj = TipoContratoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, tc_id: UUID, body: TipoContratoUpdate):
        obj = TipoContratoService.get_or_404(db, tenant_id, tc_id)
        updated = TipoContratoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, tc_id: UUID):
        obj = TipoContratoService.get_or_404(db, tenant_id, tc_id)
        TipoContratoRepository.delete(db, obj)
        db.commit()


class CausalFiniquitoService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, solo_activas: bool):
        return CausalFiniquitoRepository.get_all(db, tenant_id, solo_activas)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, causal_id: UUID):
        obj = CausalFiniquitoRepository.get_by_id(db, tenant_id, causal_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Causal de finiquito no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: CausalFiniquitoCreate):
        obj = CausalFiniquitoRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, causal_id: UUID, body: CausalFiniquitoUpdate):
        obj = CausalFiniquitoService.get_or_404(db, tenant_id, causal_id)
        updated = CausalFiniquitoRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, causal_id: UUID):
        obj = CausalFiniquitoService.get_or_404(db, tenant_id, causal_id)
        CausalFiniquitoRepository.delete(db, obj)
        db.commit()


class ClausulaAdicionalService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, solo_activas: bool):
        return ClausulaAdicionalRepository.get_all(db, tenant_id, solo_activas)

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, clausula_id: UUID):
        obj = ClausulaAdicionalRepository.get_by_id(db, tenant_id, clausula_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Cláusula adicional no encontrada.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: ClausulaAdicionalCreate):
        obj = ClausulaAdicionalRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, clausula_id: UUID, body: ClausulaAdicionalUpdate):
        obj = ClausulaAdicionalService.get_or_404(db, tenant_id, clausula_id)
        updated = ClausulaAdicionalRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, clausula_id: UUID):
        obj = ClausulaAdicionalService.get_or_404(db, tenant_id, clausula_id)
        ClausulaAdicionalRepository.delete(db, obj)
        db.commit()


class ConceptoRemuneracionService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, page: int, size: int,
             tipo: Optional[str], search: str, solo_activos: bool):
        return ConceptoRemuneracionRepository.get_all(
            db, tenant_id, page, size, tipo, search, solo_activos
        )

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, concepto_id: UUID):
        obj = ConceptoRemuneracionRepository.get_by_id(db, tenant_id, concepto_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Concepto de remuneración no encontrado.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: ConceptoRemuneracionCreate):
        if ConceptoRemuneracionRepository.get_by_codigo(db, tenant_id, body.codigo):
            raise HTTPException(status_code=400,
                                detail=f"Ya existe un concepto con código '{body.codigo}'.")
        obj = ConceptoRemuneracionRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, concepto_id: UUID,
               body: ConceptoRemuneracionUpdate):
        obj = ConceptoRemuneracionService.get_or_404(db, tenant_id, concepto_id)
        updated = ConceptoRemuneracionRepository.update(
            db, obj, body.model_dump(exclude_unset=True)
        )
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete(db: Session, tenant_id: UUID, concepto_id: UUID):
        obj = ConceptoRemuneracionService.get_or_404(db, tenant_id, concepto_id)
        ConceptoRemuneracionRepository.delete(db, obj)
        db.commit()


class ParametroMensualService:

    @staticmethod
    def list(db: Session, tenant_id: UUID, anio: Optional[int], page: int, size: int):
        return ParametroMensualRepository.get_all(db, tenant_id, anio, page, size)

    @staticmethod
    def get_vigente(db: Session, tenant_id: UUID):
        obj = ParametroMensualRepository.get_vigente(db, tenant_id)
        if not obj:
            raise HTTPException(status_code=404,
                                detail="No hay parámetros de período vigente configurados.")
        return obj

    @staticmethod
    def get_or_404(db: Session, tenant_id: UUID, anio: int, mes: int):
        obj = ParametroMensualRepository.get_by_periodo(db, tenant_id, anio, mes)
        if not obj:
            raise HTTPException(status_code=404,
                                detail=f"Parámetros no encontrados para {anio}/{mes:02d}.")
        return obj

    @staticmethod
    def create(db: Session, tenant_id: UUID, body: ParametroMensualCreate):
        if ParametroMensualRepository.get_by_periodo(db, tenant_id, body.anio, body.mes):
            raise HTTPException(status_code=400,
                                detail=f"Ya existen parámetros para {body.anio}/{body.mes:02d}.")
        obj = ParametroMensualRepository.create(db, tenant_id, body.model_dump())
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, tenant_id: UUID, anio: int, mes: int,
               body: ParametroMensualUpdate):
        obj = ParametroMensualService.get_or_404(db, tenant_id, anio, mes)
        if obj.bloqueado and not body.bloqueado:
            pass  # permitir desbloquear
        elif obj.bloqueado:
            raise HTTPException(status_code=400,
                                detail="El período está bloqueado. Desbloquee primero.")
        updated = ParametroMensualRepository.update(db, obj, body.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated)
        return updated
