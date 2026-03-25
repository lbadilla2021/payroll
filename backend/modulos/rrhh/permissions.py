"""
modulos/rrhh/permissions.py
============================
Catálogo de permisos del módulo RRHH.
Se ejecuta en bootstrap o migración para insertar en la tabla permissions.

Uso:
    from modulos.rrhh.permissions import seed_permissions
    seed_permissions(db)
"""

from sqlalchemy.orm import Session
from app.models.models import Permission

RRHH_PERMISSIONS = [
    # Supervisores
    ("rrhh.supervisores.read",   "Ver supervisores",      "rrhh"),
    ("rrhh.supervisores.create", "Crear supervisores",    "rrhh"),
    ("rrhh.supervisores.update", "Editar supervisores",   "rrhh"),
    ("rrhh.supervisores.delete", "Eliminar supervisores", "rrhh"),

    # Tipos de permiso
    ("rrhh.tipos_permiso.read",   "Ver tipos de permiso",    "rrhh"),
    ("rrhh.tipos_permiso.create", "Crear tipos de permiso",  "rrhh"),
    ("rrhh.tipos_permiso.update", "Editar tipos de permiso", "rrhh"),

    # Trabajadores
    ("rrhh.trabajadores.read",   "Ver trabajadores",      "rrhh"),
    ("rrhh.trabajadores.create", "Crear trabajadores",    "rrhh"),
    ("rrhh.trabajadores.update", "Editar trabajadores",   "rrhh"),
    ("rrhh.trabajadores.delete", "Desactivar trabajadores", "rrhh"),

    # Vacaciones
    ("rrhh.vacaciones.read",   "Ver vacaciones",      "rrhh"),
    ("rrhh.vacaciones.create", "Registrar vacaciones", "rrhh"),
    ("rrhh.vacaciones.update", "Editar vacaciones",   "rrhh"),
    ("rrhh.vacaciones.delete", "Eliminar vacaciones", "rrhh"),

    # Permisos laborales
    ("rrhh.permisos.read",   "Ver permisos laborales",      "rrhh"),
    ("rrhh.permisos.create", "Registrar permisos laborales", "rrhh"),
    ("rrhh.permisos.update", "Editar permisos laborales",   "rrhh"),
    ("rrhh.permisos.delete", "Eliminar permisos laborales", "rrhh"),

    # Evaluaciones
    ("rrhh.evaluaciones.read",   "Ver evaluaciones",      "rrhh"),
    ("rrhh.evaluaciones.create", "Crear evaluaciones",    "rrhh"),
    ("rrhh.evaluaciones.update", "Editar evaluaciones",   "rrhh"),
]


def seed_permissions(db: Session) -> int:
    """
    Inserta permisos del módulo RRHH si no existen.
    Retorna la cantidad de permisos nuevos insertados.
    """
    inserted = 0
    for code, name, module in RRHH_PERMISSIONS:
        exists = db.query(Permission).filter(Permission.code == code).first()
        if not exists:
            db.add(Permission(code=code, name=name, module=module, is_active=True))
            inserted += 1
    if inserted:
        db.commit()
    return inserted
