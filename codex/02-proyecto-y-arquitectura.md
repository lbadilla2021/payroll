# Proyecto y arquitectura

## Proyecto

Repositorio: `/workspace/payroll`.

Sistema SaaS de nómina/remuneraciones para Chile, con módulos principales:

- `frontend/`: HTML + JS modular, páginas por módulo.
- `backend/`: FastAPI/Python, módulos por dominio.
- `backend/modulos/rrhh`: ficha de trabajador, permisos, licencias, vacaciones, datos laborales y previsionales.
- `backend/modulos/nomina`: contratos, movimientos mensuales, cálculo, finiquitos, préstamos, anticipos, parámetros y catálogos.

## Frontend relevante

Páginas principales trabajadas recientemente:

- `frontend/nomina/movimientos.html`: proceso mensual y panel/modal de movimiento.
- `frontend/nomina/calculo.html`: liquidaciones y panel de desglose.
- `frontend/nomina/reportes/liquidaciones.html`: generación imprimible/PDF de liquidaciones.
- `frontend/rrhh/trabajador.html`: ficha del trabajador.
- `frontend/static/js/nav.js`: navegación lateral compartida.

Convenciones observadas:

- Las páginas suelen importar:
  - `/static/js/api.js`
  - `/static/js/auth.js`
  - `/static/js/ui.js`
  - `/static/js/toast.js`
  - `/static/js/nav.js`
- La navegación se centraliza en `frontend/static/js/nav.js`.
- El `body data-page="..."` define el ítem activo en el menú.

## Backend relevante

### Operacional de nómina

- `backend/modulos/nomina/services_operacional.py`
  - Servicios de movimientos, contratos, finiquitos, préstamos y anticipos.
  - Contiene la lógica reciente de situación del mes.

- `backend/modulos/nomina/repositories_operacional.py`
  - Repositorios de entidades operacionales.

- `backend/modulos/nomina/schemas_operacional.py`
  - Schemas Pydantic para movimientos y entidades operacionales.

- `backend/modulos/nomina/endpoints_operacional.py`
  - Endpoints `/nomina/movimientos`, contratos, finiquitos, etc.

### Motor de cálculo

- `backend/modulos/nomina/calculo/motor.py`
  - Motor de cálculo de remuneraciones.
  - Define `DatosTrabajador`, `DatosMovimiento`, `ResultadoCalculo`.
  - Contiene la fórmula de sueldo base proporcional, gratificación, descuentos, líquido.

- `backend/modulos/nomina/calculo/servicio_calculo.py`
  - Orquestador: carga trabajador, movimiento, parámetros, conceptos y ejecuta motor.

- `backend/modulos/nomina/calculo/endpoints_calculo.py`
  - Endpoints `/nomina/calculo/movimiento/{id}`, `/preview`, `/empresa`.

## Menú actual relevante

En `frontend/static/js/nav.js`, el grupo **Reportes** debe quedar entre **Nómina** y **Mantenedores**, con opción:

- `Liquidaciones PDF` → `/nomina/reportes/liquidaciones.html`

## Reportes

La página de reportes debe vivir en:

- `frontend/nomina/reportes/liquidaciones.html`

No usar `frontend/nomina/reportes.html` para nuevas mejoras; esa ruta fue reemplazada por la subcarpeta `reportes/`.
