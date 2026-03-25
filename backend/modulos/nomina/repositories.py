"""
modulos/nomina/repositories.py
==============================
Capa de acceso a datos para Nómina.

Catálogos globales: sin tenant_id, queries simples.
Operacionales: con tenant_id + SET LOCAL para RLS.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from modulos.nomina.models import (
    Afp, Banco, CausalFiniquito, Ccaf, CentroCosto, ClausulaAdicional,
    Cargo, ConceptoRemuneracion, EmpresaConfig, FactorActualizacion,
    Isapre, Mutualidad, ParametroMensual, Region, Comuna,
    ServMedCchc, Sucursal, TipoContrato, TipoMoneda,
    TipoMovimientoBancario, TramoAsignacionFamiliar, TramoImpuestoUnicoUTM,
)


def _set_tenant(db: Session, tenant_id: UUID) -> None:
    db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": str(tenant_id)})


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS GLOBALES (sin tenant_id)
# ─────────────────────────────────────────────────────────────────────────────

class AfpRepository:

    @staticmethod
    def get_all(db: Session, solo_activas: bool = True) -> list[Afp]:
        q = db.query(Afp)
        if solo_activas:
            q = q.filter(Afp.es_activa == True)
        return q.order_by(Afp.nombre).all()

    @staticmethod
    def get_by_id(db: Session, afp_id: int) -> Optional[Afp]:
        return db.query(Afp).filter(Afp.id == afp_id).first()

    @staticmethod
    def update(db: Session, obj: Afp, data: dict) -> Afp:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class IsapreRepository:

    @staticmethod
    def get_all(db: Session, solo_activas: bool = True) -> list[Isapre]:
        q = db.query(Isapre)
        if solo_activas:
            q = q.filter(Isapre.es_activa == True)
        return q.order_by(Isapre.nombre).all()

    @staticmethod
    def get_by_id(db: Session, isapre_id: int) -> Optional[Isapre]:
        return db.query(Isapre).filter(Isapre.id == isapre_id).first()

    @staticmethod
    def update(db: Session, obj: Isapre, data: dict) -> Isapre:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class CcafRepository:

    @staticmethod
    def get_all(db: Session, solo_activas: bool = True) -> list[Ccaf]:
        q = db.query(Ccaf)
        if solo_activas:
            q = q.filter(Ccaf.es_activa == True)
        return q.order_by(Ccaf.nombre).all()

    @staticmethod
    def get_by_id(db: Session, ccaf_id: int) -> Optional[Ccaf]:
        return db.query(Ccaf).filter(Ccaf.id == ccaf_id).first()


class MutualidadRepository:

    @staticmethod
    def get_all(db: Session, solo_activas: bool = True) -> list[Mutualidad]:
        q = db.query(Mutualidad)
        if solo_activas:
            q = q.filter(Mutualidad.es_activa == True)
        return q.order_by(Mutualidad.nombre).all()

    @staticmethod
    def get_by_id(db: Session, mut_id: int) -> Optional[Mutualidad]:
        return db.query(Mutualidad).filter(Mutualidad.id == mut_id).first()


class BancoRepository:

    @staticmethod
    def get_all(db: Session, solo_activos: bool = True) -> list[Banco]:
        q = db.query(Banco)
        if solo_activos:
            q = q.filter(Banco.es_activo == True)
        return q.order_by(Banco.nombre).all()

    @staticmethod
    def get_by_id(db: Session, banco_id: int) -> Optional[Banco]:
        return db.query(Banco).filter(Banco.id == banco_id).first()


class TipoMovimientoBancarioRepository:

    @staticmethod
    def get_all(db: Session) -> list[TipoMovimientoBancario]:
        return db.query(TipoMovimientoBancario).order_by(TipoMovimientoBancario.id).all()


class RegionRepository:

    @staticmethod
    def get_all(db: Session, solo_zona_extrema: bool = False) -> list[Region]:
        q = db.query(Region)
        if solo_zona_extrema:
            q = q.filter(Region.es_zona_extrema == True)
        return q.order_by(Region.nombre).all()

    @staticmethod
    def get_by_id(db: Session, region_id: int) -> Optional[Region]:
        return db.query(Region).filter(Region.id == region_id).first()


class ComunaRepository:

    @staticmethod
    def get_all(db: Session, region_id: Optional[int] = None) -> list[Comuna]:
        q = db.query(Comuna)
        if region_id:
            q = q.filter(Comuna.region_id == region_id)
        return q.order_by(Comuna.nombre).all()

    @staticmethod
    def get_by_codigo(db: Session, codigo: int) -> Optional[Comuna]:
        return db.query(Comuna).filter(Comuna.codigo == codigo).first()


class TipoMonedaRepository:

    @staticmethod
    def get_all(db: Session, solo_activas: bool = True) -> list[TipoMoneda]:
        q = db.query(TipoMoneda)
        if solo_activas:
            q = q.filter(TipoMoneda.es_activa == True)
        return q.order_by(TipoMoneda.codigo).all()

    @staticmethod
    def get_by_id(db: Session, moneda_id: int) -> Optional[TipoMoneda]:
        return db.query(TipoMoneda).filter(TipoMoneda.id == moneda_id).first()


class TramoAsignacionFamiliarRepository:

    @staticmethod
    def get_by_periodo(db: Session, anio: int, mes: int) -> list[TramoAsignacionFamiliar]:
        return db.query(TramoAsignacionFamiliar).filter(
            TramoAsignacionFamiliar.anio == anio,
            TramoAsignacionFamiliar.mes == mes
        ).order_by(TramoAsignacionFamiliar.tramo).all()

    @staticmethod
    def get_ultimo_periodo(db: Session) -> list[TramoAsignacionFamiliar]:
        """Retorna los tramos del período más reciente disponible."""
        ultimo = db.query(
            TramoAsignacionFamiliar.anio,
            TramoAsignacionFamiliar.mes
        ).order_by(
            TramoAsignacionFamiliar.anio.desc(),
            TramoAsignacionFamiliar.mes.desc()
        ).first()
        if not ultimo:
            return []
        return TramoAsignacionFamiliarRepository.get_by_periodo(db, ultimo.anio, ultimo.mes)

    @staticmethod
    def create(db: Session, data: dict) -> TramoAsignacionFamiliar:
        obj = TramoAsignacionFamiliar(**data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_periodo(db: Session, anio: int, mes: int) -> int:
        """Elimina todos los tramos de un período (para reemplazar)."""
        deleted = db.query(TramoAsignacionFamiliar).filter(
            TramoAsignacionFamiliar.anio == anio,
            TramoAsignacionFamiliar.mes == mes
        ).delete()
        db.flush()
        return deleted


class TramoImpuestoUnicoRepository:

    @staticmethod
    def get_by_periodo(db: Session, anio: int, mes: int) -> list[TramoImpuestoUnicoUTM]:
        return db.query(TramoImpuestoUnicoUTM).filter(
            TramoImpuestoUnicoUTM.anio == anio,
            TramoImpuestoUnicoUTM.mes == mes
        ).order_by(TramoImpuestoUnicoUTM.orden).all()

    @staticmethod
    def get_ultimo_periodo(db: Session) -> list[TramoImpuestoUnicoUTM]:
        ultimo = db.query(
            TramoImpuestoUnicoUTM.anio,
            TramoImpuestoUnicoUTM.mes
        ).order_by(
            TramoImpuestoUnicoUTM.anio.desc(),
            TramoImpuestoUnicoUTM.mes.desc()
        ).first()
        if not ultimo:
            return []
        return TramoImpuestoUnicoRepository.get_by_periodo(db, ultimo.anio, ultimo.mes)

    @staticmethod
    def create(db: Session, data: dict) -> TramoImpuestoUnicoUTM:
        obj = TramoImpuestoUnicoUTM(**data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_periodo(db: Session, anio: int, mes: int) -> int:
        deleted = db.query(TramoImpuestoUnicoUTM).filter(
            TramoImpuestoUnicoUTM.anio == anio,
            TramoImpuestoUnicoUTM.mes == mes
        ).delete()
        db.flush()
        return deleted


class FactorActualizacionRepository:

    @staticmethod
    def get_all(db: Session, anio: Optional[int] = None) -> list[FactorActualizacion]:
        q = db.query(FactorActualizacion)
        if anio:
            q = q.filter(FactorActualizacion.anio == anio)
        return q.order_by(FactorActualizacion.anio.desc(), FactorActualizacion.mes.desc()).all()

    @staticmethod
    def get_by_periodo(db: Session, anio: int, mes: int) -> Optional[FactorActualizacion]:
        return db.query(FactorActualizacion).filter(
            FactorActualizacion.anio == anio,
            FactorActualizacion.mes == mes
        ).first()

    @staticmethod
    def get_vigente(db: Session) -> Optional[FactorActualizacion]:
        """Retorna el factor del período más reciente."""
        return db.query(FactorActualizacion).order_by(
            FactorActualizacion.anio.desc(),
            FactorActualizacion.mes.desc()
        ).first()

    @staticmethod
    def create(db: Session, data: dict) -> FactorActualizacion:
        obj = FactorActualizacion(**data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: FactorActualizacion, data: dict) -> FactorActualizacion:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class ServMedCchcRepository:

    @staticmethod
    def get_by_periodo(db: Session, anio: int, mes: int) -> Optional[ServMedCchc]:
        return db.query(ServMedCchc).filter(
            ServMedCchc.anio == anio,
            ServMedCchc.mes == mes
        ).first()

    @staticmethod
    def get_vigente(db: Session) -> Optional[ServMedCchc]:
        return db.query(ServMedCchc).order_by(
            ServMedCchc.anio.desc(),
            ServMedCchc.mes.desc()
        ).first()

    @staticmethod
    def create(db: Session, data: dict) -> ServMedCchc:
        obj = ServMedCchc(**data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: ServMedCchc, data: dict) -> ServMedCchc:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# OPERACIONALES (con tenant_id + RLS)
# ─────────────────────────────────────────────────────────────────────────────

class EmpresaConfigRepository:

    @staticmethod
    def get(db: Session, tenant_id: UUID) -> Optional[EmpresaConfig]:
        _set_tenant(db, tenant_id)
        return db.query(EmpresaConfig).filter(
            EmpresaConfig.tenant_id == tenant_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> EmpresaConfig:
        _set_tenant(db, tenant_id)
        obj = EmpresaConfig(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: EmpresaConfig, data: dict) -> EmpresaConfig:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj


class SucursalRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 50,
                solo_activas: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(Sucursal).filter(Sucursal.tenant_id == tenant_id)
        if solo_activas:
            q = q.filter(Sucursal.es_activa == True)
        total = q.count()
        items = q.order_by(Sucursal.nombre).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, sucursal_id: UUID) -> Optional[Sucursal]:
        _set_tenant(db, tenant_id)
        return db.query(Sucursal).filter(
            Sucursal.tenant_id == tenant_id,
            Sucursal.id == sucursal_id
        ).first()

    @staticmethod
    def get_by_codigo(db: Session, tenant_id: UUID, codigo: str) -> Optional[Sucursal]:
        _set_tenant(db, tenant_id)
        return db.query(Sucursal).filter(
            Sucursal.tenant_id == tenant_id,
            Sucursal.codigo == codigo
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Sucursal:
        _set_tenant(db, tenant_id)
        obj = Sucursal(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Sucursal, data: dict) -> Sucursal:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Sucursal) -> None:
        db.delete(obj)
        db.flush()


class CentroCostoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 50,
                solo_activos: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(CentroCosto).filter(CentroCosto.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(CentroCosto.es_activo == True)
        total = q.count()
        items = q.order_by(CentroCosto.descripcion).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, cc_id: UUID) -> Optional[CentroCosto]:
        _set_tenant(db, tenant_id)
        return db.query(CentroCosto).filter(
            CentroCosto.tenant_id == tenant_id,
            CentroCosto.id == cc_id
        ).first()

    @staticmethod
    def get_by_codigo(db: Session, tenant_id: UUID, codigo: str) -> Optional[CentroCosto]:
        _set_tenant(db, tenant_id)
        return db.query(CentroCosto).filter(
            CentroCosto.tenant_id == tenant_id,
            CentroCosto.codigo == codigo
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> CentroCosto:
        _set_tenant(db, tenant_id)
        obj = CentroCosto(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: CentroCosto, data: dict) -> CentroCosto:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: CentroCosto) -> None:
        db.delete(obj)
        db.flush()


class CargoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 50,
                search: str = "", solo_activos: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(Cargo).filter(Cargo.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(Cargo.es_activo == True)
        if search:
            q = q.filter(Cargo.descripcion.ilike(f"%{search}%"))
        total = q.count()
        items = q.order_by(Cargo.descripcion).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, cargo_id: UUID) -> Optional[Cargo]:
        _set_tenant(db, tenant_id)
        return db.query(Cargo).filter(
            Cargo.tenant_id == tenant_id,
            Cargo.id == cargo_id
        ).first()

    @staticmethod
    def get_by_codigo(db: Session, tenant_id: UUID, codigo: str) -> Optional[Cargo]:
        _set_tenant(db, tenant_id)
        return db.query(Cargo).filter(
            Cargo.tenant_id == tenant_id,
            Cargo.codigo == codigo
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> Cargo:
        _set_tenant(db, tenant_id)
        obj = Cargo(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Cargo, data: dict) -> Cargo:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Cargo) -> None:
        db.delete(obj)
        db.flush()


class TipoContratoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, solo_activos: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(TipoContrato).filter(TipoContrato.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(TipoContrato.es_activo == True)
        return q.order_by(TipoContrato.descripcion).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, tc_id: UUID) -> Optional[TipoContrato]:
        _set_tenant(db, tenant_id)
        return db.query(TipoContrato).filter(
            TipoContrato.tenant_id == tenant_id,
            TipoContrato.id == tc_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> TipoContrato:
        _set_tenant(db, tenant_id)
        obj = TipoContrato(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: TipoContrato, data: dict) -> TipoContrato:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: TipoContrato) -> None:
        db.delete(obj)
        db.flush()


class CausalFiniquitoRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, solo_activas: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(CausalFiniquito).filter(CausalFiniquito.tenant_id == tenant_id)
        if solo_activas:
            q = q.filter(CausalFiniquito.es_activa == True)
        return q.order_by(CausalFiniquito.codigo).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, causal_id: UUID) -> Optional[CausalFiniquito]:
        _set_tenant(db, tenant_id)
        return db.query(CausalFiniquito).filter(
            CausalFiniquito.tenant_id == tenant_id,
            CausalFiniquito.id == causal_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> CausalFiniquito:
        _set_tenant(db, tenant_id)
        obj = CausalFiniquito(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: CausalFiniquito, data: dict) -> CausalFiniquito:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: CausalFiniquito) -> None:
        db.delete(obj)
        db.flush()


class ClausulaAdicionalRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, solo_activas: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(ClausulaAdicional).filter(ClausulaAdicional.tenant_id == tenant_id)
        if solo_activas:
            q = q.filter(ClausulaAdicional.es_activa == True)
        return q.order_by(ClausulaAdicional.codigo).all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, clausula_id: UUID) -> Optional[ClausulaAdicional]:
        _set_tenant(db, tenant_id)
        return db.query(ClausulaAdicional).filter(
            ClausulaAdicional.tenant_id == tenant_id,
            ClausulaAdicional.id == clausula_id
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> ClausulaAdicional:
        _set_tenant(db, tenant_id)
        obj = ClausulaAdicional(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: ClausulaAdicional, data: dict) -> ClausulaAdicional:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: ClausulaAdicional) -> None:
        db.delete(obj)
        db.flush()


class ConceptoRemuneracionRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, page: int = 1, size: int = 50,
                tipo: Optional[str] = None, search: str = "", solo_activos: bool = True):
        _set_tenant(db, tenant_id)
        q = db.query(ConceptoRemuneracion).filter(ConceptoRemuneracion.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(ConceptoRemuneracion.es_activo == True)
        if tipo in ("H", "D"):
            q = q.filter(ConceptoRemuneracion.tipo == tipo)
        if search:
            q = q.filter(
                ConceptoRemuneracion.descripcion.ilike(f"%{search}%") |
                ConceptoRemuneracion.codigo.ilike(f"%{search}%")
            )
        total = q.count()
        items = q.order_by(ConceptoRemuneracion.tipo, ConceptoRemuneracion.codigo)\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID, concepto_id: UUID) -> Optional[ConceptoRemuneracion]:
        _set_tenant(db, tenant_id)
        return db.query(ConceptoRemuneracion).filter(
            ConceptoRemuneracion.tenant_id == tenant_id,
            ConceptoRemuneracion.id == concepto_id
        ).first()

    @staticmethod
    def get_by_codigo(db: Session, tenant_id: UUID, codigo: str) -> Optional[ConceptoRemuneracion]:
        _set_tenant(db, tenant_id)
        return db.query(ConceptoRemuneracion).filter(
            ConceptoRemuneracion.tenant_id == tenant_id,
            ConceptoRemuneracion.codigo == codigo
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> ConceptoRemuneracion:
        _set_tenant(db, tenant_id)
        obj = ConceptoRemuneracion(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: ConceptoRemuneracion, data: dict) -> ConceptoRemuneracion:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: ConceptoRemuneracion) -> None:
        db.delete(obj)
        db.flush()


class ParametroMensualRepository:

    @staticmethod
    def get_all(db: Session, tenant_id: UUID, anio: Optional[int] = None,
                page: int = 1, size: int = 24):
        _set_tenant(db, tenant_id)
        q = db.query(ParametroMensual).filter(ParametroMensual.tenant_id == tenant_id)
        if anio:
            q = q.filter(ParametroMensual.anio == anio)
        total = q.count()
        items = q.order_by(ParametroMensual.anio.desc(), ParametroMensual.mes.desc())\
                  .offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_by_periodo(db: Session, tenant_id: UUID, anio: int,
                       mes: int) -> Optional[ParametroMensual]:
        _set_tenant(db, tenant_id)
        return db.query(ParametroMensual).filter(
            ParametroMensual.tenant_id == tenant_id,
            ParametroMensual.anio == anio,
            ParametroMensual.mes == mes
        ).first()

    @staticmethod
    def get_vigente(db: Session, tenant_id: UUID) -> Optional[ParametroMensual]:
        _set_tenant(db, tenant_id)
        return db.query(ParametroMensual).filter(
            ParametroMensual.tenant_id == tenant_id,
            ParametroMensual.cerrado == False
        ).order_by(
            ParametroMensual.anio.desc(),
            ParametroMensual.mes.desc()
        ).first()

    @staticmethod
    def create(db: Session, tenant_id: UUID, data: dict) -> ParametroMensual:
        _set_tenant(db, tenant_id)
        obj = ParametroMensual(tenant_id=tenant_id, **data)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: ParametroMensual, data: dict) -> ParametroMensual:
        for k, v in data.items():
            setattr(obj, k, v)
        db.flush()
        db.refresh(obj)
        return obj
