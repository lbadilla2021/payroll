"""
modulos/nomina/permissions.py
=============================
Catálogo completo de permisos del módulo Nómina.
Iteración 2 + Iteración 3.
Los catálogos globales (AFP, isapres, etc.) no requieren permiso de tenant
— cualquier usuario autenticado puede leerlos.
Las tablas operacionales sí requieren permiso específico.
"""

from sqlalchemy.orm import Session
from app.models.models import Permission

NOMINA_PERMISSIONS = [
    # Empresa config
    ("nomina.empresa.read",   "Ver configuración empresa",    "nomina"),
    ("nomina.empresa.update", "Editar configuración empresa", "nomina"),

    # Sucursales
    ("nomina.sucursales.read",   "Ver sucursales",      "nomina"),
    ("nomina.sucursales.create", "Crear sucursales",    "nomina"),
    ("nomina.sucursales.update", "Editar sucursales",   "nomina"),
    ("nomina.sucursales.delete", "Eliminar sucursales", "nomina"),

    # Centros de costo
    ("nomina.centros_costo.read",   "Ver centros de costo",      "nomina"),
    ("nomina.centros_costo.create", "Crear centros de costo",    "nomina"),
    ("nomina.centros_costo.update", "Editar centros de costo",   "nomina"),
    ("nomina.centros_costo.delete", "Eliminar centros de costo", "nomina"),

    # Cargos
    ("nomina.cargos.read",   "Ver cargos",      "nomina"),
    ("nomina.cargos.create", "Crear cargos",    "nomina"),
    ("nomina.cargos.update", "Editar cargos",   "nomina"),
    ("nomina.cargos.delete", "Eliminar cargos", "nomina"),

    # Tipos de contrato
    ("nomina.tipos_contrato.read",   "Ver tipos de contrato",      "nomina"),
    ("nomina.tipos_contrato.create", "Crear tipos de contrato",    "nomina"),
    ("nomina.tipos_contrato.update", "Editar tipos de contrato",   "nomina"),
    ("nomina.tipos_contrato.delete", "Eliminar tipos de contrato", "nomina"),

    # Causales de finiquito
    ("nomina.causales_finiquito.read",   "Ver causales de finiquito",      "nomina"),
    ("nomina.causales_finiquito.create", "Crear causales de finiquito",    "nomina"),
    ("nomina.causales_finiquito.update", "Editar causales de finiquito",   "nomina"),
    ("nomina.causales_finiquito.delete", "Eliminar causales de finiquito", "nomina"),

    # Cláusulas adicionales
    ("nomina.clausulas.read",   "Ver cláusulas adicionales",      "nomina"),
    ("nomina.clausulas.create", "Crear cláusulas adicionales",    "nomina"),
    ("nomina.clausulas.update", "Editar cláusulas adicionales",   "nomina"),
    ("nomina.clausulas.delete", "Eliminar cláusulas adicionales", "nomina"),

    # Conceptos de remuneración (haberes y descuentos)
    ("nomina.conceptos.read",   "Ver conceptos de remuneración",      "nomina"),
    ("nomina.conceptos.create", "Crear conceptos de remuneración",    "nomina"),
    ("nomina.conceptos.update", "Editar conceptos de remuneración",   "nomina"),
    ("nomina.conceptos.delete", "Eliminar conceptos de remuneración", "nomina"),

    # Parámetros mensuales
    ("nomina.parametros.read",   "Ver parámetros mensuales",    "nomina"),
    ("nomina.parametros.create", "Crear parámetros mensuales",  "nomina"),
    ("nomina.parametros.update", "Editar parámetros mensuales", "nomina"),

    # ── Iteración 3 ──────────────────────────────────────────────────────────
    # Contratos de trabajo
    ("nomina.contratos.read",   "Ver contratos de trabajo",      "nomina"),
    ("nomina.contratos.create", "Crear contratos de trabajo",    "nomina"),
    ("nomina.contratos.update", "Editar contratos de trabajo",   "nomina"),
    ("nomina.contratos.delete", "Eliminar contratos de trabajo", "nomina"),

    # Movimientos mensuales
    ("nomina.movimientos.read",   "Ver movimientos mensuales",      "nomina"),
    ("nomina.movimientos.create", "Crear movimientos mensuales",    "nomina"),
    ("nomina.movimientos.update", "Editar movimientos mensuales",   "nomina"),
    ("nomina.movimientos.delete", "Eliminar movimientos mensuales", "nomina"),

    # Finiquitos
    ("nomina.finiquitos.read",   "Ver finiquitos",      "nomina"),
    ("nomina.finiquitos.create", "Crear finiquitos",    "nomina"),
    ("nomina.finiquitos.update", "Editar finiquitos",   "nomina"),
    ("nomina.finiquitos.delete", "Eliminar finiquitos", "nomina"),

    # Préstamos
    ("nomina.prestamos.read",   "Ver préstamos a trabajadores",    "nomina"),
    ("nomina.prestamos.create", "Crear préstamos a trabajadores",  "nomina"),
    ("nomina.prestamos.update", "Editar préstamos a trabajadores", "nomina"),
    ("nomina.prestamos.delete", "Cancelar préstamos",              "nomina"),

    # Anticipos
    ("nomina.anticipos.read",   "Ver anticipos de remuneraciones",    "nomina"),
    ("nomina.anticipos.create", "Crear anticipos de remuneraciones",  "nomina"),
    ("nomina.anticipos.update", "Editar anticipos de remuneraciones", "nomina"),
    ("nomina.anticipos.delete", "Anular anticipos de remuneraciones", "nomina"),

    # ── Iteración 4 ──────────────────────────────────────────────────────────
    # Motor de cálculo
    ("nomina.calculo.ejecutar", "Ejecutar cálculo de liquidaciones", "nomina"),
]


def seed_permissions(db: Session) -> int:
    """
    Inserta permisos del módulo Nómina si no existen.
    Retorna la cantidad de permisos nuevos insertados.
    """
    inserted = 0
    for code, name, module in NOMINA_PERMISSIONS:
        exists = db.query(Permission).filter(Permission.code == code).first()
        if not exists:
            db.add(Permission(code=code, name=name, module=module, is_active=True))
            inserted += 1
    if inserted:
        db.commit()
    return inserted
