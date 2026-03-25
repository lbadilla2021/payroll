# modulos/rrhh/__init__.py
from modulos.rrhh.models import (
    # Catálogos globales
    TipoPermisoGlobal, TipoCargoRrhhGlobal,
    # Operacionales
    Supervisor, TipoPermiso,
    AtributoEvalCuantitativa, EvaluacionCuantitativa,
    AtributoEvalCualitativa, EvaluacionCualitativa,
    # Trabajador y subentidades
    Trabajador, TrabajadorApv, TrabajadorConyugeAfiliado,
    CargaFamiliar, CargaFamiliarSueldoMensual,
    FichaVacacion, FichaPermiso, FichaPrestamo,
    CargoDesempenado, Observacion,
    TrabajadorEvalCuantitativa, TrabajadorEvalCualitativa,
    ContratoRrhh,
)

__all__ = [
    "TipoPermisoGlobal", "TipoCargoRrhhGlobal",
    "Supervisor", "TipoPermiso",
    "AtributoEvalCuantitativa", "EvaluacionCuantitativa",
    "AtributoEvalCualitativa", "EvaluacionCualitativa",
    "Trabajador", "TrabajadorApv", "TrabajadorConyugeAfiliado",
    "CargaFamiliar", "CargaFamiliarSueldoMensual",
    "FichaVacacion", "FichaPermiso", "FichaPrestamo",
    "CargoDesempenado", "Observacion",
    "TrabajadorEvalCuantitativa", "TrabajadorEvalCualitativa",
    "ContratoRrhh",
]
