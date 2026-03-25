# modulos/nomina/__init__.py
from modulos.nomina.models import (
    # Catálogos globales
    Afp, Isapre, Ccaf, Mutualidad, Banco, TipoMovimientoBancario,
    Region, Comuna, TipoMoneda,
    TramoAsignacionFamiliar, TramoImpuestoUnicoUTM,
    FactorActualizacion, ServMedCchc,
    # Operacionales
    EmpresaConfig, Sucursal, CentroCosto, Cargo,
    TipoContrato, CausalFiniquito, ClausulaAdicional,
    ConceptoRemuneracion, ParametroMensual,
    MovimientoMensual, MovimientoConcepto,
    Contrato, ContratoClausula, Finiquito, FiniquitoConcepto,
    Prestamo, PrestamoCuota, Anticipo,
    CertificadoImpuesto, RetencionAnual, LreGeneracion,
)

__all__ = [
    "Afp", "Isapre", "Ccaf", "Mutualidad", "Banco", "TipoMovimientoBancario",
    "Region", "Comuna", "TipoMoneda",
    "TramoAsignacionFamiliar", "TramoImpuestoUnicoUTM",
    "FactorActualizacion", "ServMedCchc",
    "EmpresaConfig", "Sucursal", "CentroCosto", "Cargo",
    "TipoContrato", "CausalFiniquito", "ClausulaAdicional",
    "ConceptoRemuneracion", "ParametroMensual",
    "MovimientoMensual", "MovimientoConcepto",
    "Contrato", "ContratoClausula", "Finiquito", "FiniquitoConcepto",
    "Prestamo", "PrestamoCuota", "Anticipo",
    "CertificadoImpuesto", "RetencionAnual", "LreGeneracion",
]
