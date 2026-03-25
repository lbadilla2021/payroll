# modulos/__init__.py
"""
Módulos del sistema Payroll.

Estructura:
    modulos/
    ├── rrhh/       → Datos de trabajadores (personales, laborales, fichas RRHH)
    └── nomina/     → Remuneraciones (AFP, isapres, conceptos, liquidaciones, etc.)

Integración con proyecto base:
    - Usan Base de app.db.session (mismo metadata de SQLAlchemy)
    - Usan RLS mediante current_setting('app.current_tenant_id')
    - FK a public.tenants y public.users sin schema prefix en string FK
    - FK cross-módulo: "nomina.<tabla>.id" / "rrhh.<tabla>.id"

Orden de aplicación de schemas:
    1. public (tenants, users, roles - proyecto raíz)
    2. nomina (catálogos y operacional nómina)
    3. rrhh   (trabajadores y fichas RRHH)
"""
