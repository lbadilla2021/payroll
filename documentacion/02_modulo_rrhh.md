# Módulo RRHH

## Descripción general

El módulo RRHH gestiona la ficha completa del trabajador: datos personales, laborales, previsionales y toda la información de soporte necesaria para el proceso de remuneraciones. Es el origen de datos para el módulo Nómina.

**Stack:** FastAPI · SQLAlchemy · PostgreSQL (schema `rrhh`) · RLS por tenant

---

## Estructura de archivos

```
modulos/rrhh/
├── models.py          ← Modelos SQLAlchemy (schema rrhh.*)
├── schemas.py         ← Schemas Pydantic (Create / Update / Read)
├── repositories.py    ← Acceso a datos con RLS
├── services.py        ← Lógica de negocio
├── endpoints.py       ← Rutas FastAPI (~50 rutas)
├── permissions.py     ← 22 permisos RBAC + seed
└── schema.sql         ← DDL de referencia
```

---

## Base de datos

### Tablas operacionales (schema `rrhh`)

Todas las tablas tienen `tenant_id` con RLS habilitado (`app.current_tenant_id`).

| Tabla | Descripción |
|-------|-------------|
| `supervisor` | Supervisores del tenant |
| `tipo_permiso` | Tipos de permiso laboral configurables |
| `evaluacion_cuantitativa` | Catálogo de evaluaciones numéricas |
| `atributo_eval_cuantitativa` | Atributos para evaluaciones numéricas |
| `evaluacion_cualitativa` | Catálogo de evaluaciones descriptivas |
| `atributo_eval_cualitativa` | Atributos para evaluaciones descriptivas |
| `trabajador` | Ficha central del trabajador |
| `trabajador_apv` | APV individual y colectivo por trabajador |
| `trabajador_conyuge_afiliado` | Cónyuge como afiliado voluntario AFP |
| `carga_familiar` | Cargas familiares vigentes |
| `carga_familiar_sueldo_mensual` | Sueldo mensual para cálculo AF proporcional |
| `ficha_vacacion` | Registro de vacaciones otorgadas/utilizadas |
| `ficha_permiso` | Registro de permisos laborales |
| `ficha_prestamo` | Préstamos registrados en ficha RRHH |
| `cargo_desempenado` | Historial de cargos del trabajador |
| `observacion` | Observaciones generales del trabajador |
| `trabajador_eval_cuantitativa` | Evaluaciones numéricas aplicadas |
| `trabajador_eval_cualitativa` | Evaluaciones cualitativas aplicadas |
| `contrato_rrhh` | Vista histórica RRHH de contratos |

### Ficha del trabajador — campos principales

**Datos personales:** `rut`, `nombres`, `apellido_paterno`, `apellido_materno`, `fecha_nacimiento`, `email`, `telefono`, `region_id`, `comuna_id`, `estado_civil`, `sexo`, `es_extranjero`, `nacionalidad`

**Datos laborales:** `tipo_sueldo` (M/D/H/E), `monto_sueldo`, `horas_semana`, `dias_semana`, `tipo_gratificacion`, `monto_movilizacion`, `monto_colacion`, `forma_pago`, `banco_id`, `nro_cuenta`, `cargo_id`, `sucursal_id`, `centro_costo_id`, `supervisor_id`, `tipo_contrato_id`, `fecha_contrato`

**Datos previsionales:** `regimen_previsional`, `afp_id`, `cotizacion_voluntaria_afp`, `regimen_salud`, `isapre_id`, `modalidad_isapre`, `monto_isapre_pesos`, `monto_isapre_uf`, `tiene_seg_cesantia`, `contrato_plazo_fijo`, `no_cotiza_sis`, `pct_asignacion_zona`, `tipo_trabajador`

---

## API — Endpoints

Todas las rutas tienen prefijo `/api/v1`.

### Supervisores

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/supervisores` | `rrhh.supervisores.read` |
| `POST` | `/rrhh/supervisores` | `rrhh.supervisores.create` |
| `GET` | `/rrhh/supervisores/{id}` | `rrhh.supervisores.read` |
| `PATCH` | `/rrhh/supervisores/{id}` | `rrhh.supervisores.update` |
| `DELETE` | `/rrhh/supervisores/{id}` | `rrhh.supervisores.delete` |

### Tipos de Permiso Laboral

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/tipos-permiso` | `rrhh.tipos_permiso.read` |
| `POST` | `/rrhh/tipos-permiso` | `rrhh.tipos_permiso.create` |
| `PATCH` | `/rrhh/tipos-permiso/{id}` | `rrhh.tipos_permiso.update` |

### Catálogos de Evaluaciones

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/evaluaciones/cuantitativas` | `rrhh.evaluaciones.read` |
| `POST` | `/rrhh/evaluaciones/cuantitativas` | `rrhh.evaluaciones.create` |
| `PATCH` | `/rrhh/evaluaciones/cuantitativas/{id}` | `rrhh.evaluaciones.update` |
| `GET` | `/rrhh/evaluaciones/cuantitativas/atributos` | `rrhh.evaluaciones.read` |
| `POST` | `/rrhh/evaluaciones/cuantitativas/atributos` | `rrhh.evaluaciones.create` |
| `GET` | `/rrhh/evaluaciones/cualitativas` | `rrhh.evaluaciones.read` |
| `POST` | `/rrhh/evaluaciones/cualitativas` | `rrhh.evaluaciones.create` |
| `GET` | `/rrhh/evaluaciones/cualitativas/atributos` | `rrhh.evaluaciones.read` |
| `POST` | `/rrhh/evaluaciones/cualitativas/atributos` | `rrhh.evaluaciones.create` |

### Trabajadores

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores` | `rrhh.trabajadores.read` |
| `POST` | `/rrhh/trabajadores` | `rrhh.trabajadores.create` |
| `GET` | `/rrhh/trabajadores/{id}` | `rrhh.trabajadores.read` |
| `PATCH` | `/rrhh/trabajadores/{id}` | `rrhh.trabajadores.update` |
| `PATCH` | `/rrhh/trabajadores/{id}/desactivar` | `rrhh.trabajadores.delete` |

**Filtros disponibles en listado:** `search`, `solo_activos`, `sucursal_id`, `centro_costo_id`, `cargo_id`

### APV del Trabajador

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/apv` | `rrhh.trabajadores.read` |
| `POST` | `/rrhh/trabajadores/{id}/apv` | `rrhh.trabajadores.update` |
| `PATCH` | `/rrhh/trabajadores/{id}/apv/{apv_id}` | `rrhh.trabajadores.update` |
| `DELETE` | `/rrhh/trabajadores/{id}/apv/{apv_id}` | `rrhh.trabajadores.update` |

### Cónyuge Afiliado

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/conyuge` | `rrhh.trabajadores.read` |
| `PUT` | `/rrhh/trabajadores/{id}/conyuge` | `rrhh.trabajadores.update` |
| `DELETE` | `/rrhh/trabajadores/{id}/conyuge` | `rrhh.trabajadores.update` |

### Cargas Familiares

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/cargas` | `rrhh.trabajadores.read` |
| `POST` | `/rrhh/trabajadores/{id}/cargas` | `rrhh.trabajadores.update` |
| `PATCH` | `/rrhh/trabajadores/{id}/cargas/{carga_id}` | `rrhh.trabajadores.update` |

### Vacaciones

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/vacaciones` | `rrhh.vacaciones.read` |
| `POST` | `/rrhh/trabajadores/{id}/vacaciones` | `rrhh.vacaciones.create` |
| `PATCH` | `/rrhh/trabajadores/{id}/vacaciones/{vac_id}` | `rrhh.vacaciones.update` |
| `DELETE` | `/rrhh/trabajadores/{id}/vacaciones/{vac_id}` | `rrhh.vacaciones.delete` |
| `GET` | `/rrhh/trabajadores/{id}/vacaciones/resumen` | `rrhh.vacaciones.read` |

### Permisos Laborales

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/permisos` | `rrhh.permisos.read` |
| `POST` | `/rrhh/trabajadores/{id}/permisos` | `rrhh.permisos.create` |
| `PATCH` | `/rrhh/trabajadores/{id}/permisos/{permiso_id}` | `rrhh.permisos.update` |
| `DELETE` | `/rrhh/trabajadores/{id}/permisos/{permiso_id}` | `rrhh.permisos.delete` |

### Observaciones

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/observaciones` | `rrhh.trabajadores.read` |
| `POST` | `/rrhh/trabajadores/{id}/observaciones` | `rrhh.trabajadores.update` |
| `PATCH` | `/rrhh/trabajadores/{id}/observaciones/{obs_id}` | `rrhh.trabajadores.update` |
| `DELETE` | `/rrhh/trabajadores/{id}/observaciones/{obs_id}` | `rrhh.trabajadores.update` |

### Cargos Desempeñados

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/cargos-desempenados` | `rrhh.trabajadores.read` |
| `POST` | `/rrhh/trabajadores/{id}/cargos-desempenados` | `rrhh.trabajadores.update` |
| `PATCH` | `/rrhh/trabajadores/{id}/cargos-desempenados/{cargo_id}` | `rrhh.trabajadores.update` |

### Evaluaciones del Trabajador

| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/rrhh/trabajadores/{id}/evaluaciones/cuantitativas` | `rrhh.evaluaciones.read` |
| `POST` | `/rrhh/trabajadores/{id}/evaluaciones/cuantitativas` | `rrhh.evaluaciones.create` |
| `GET` | `/rrhh/trabajadores/{id}/evaluaciones/cualitativas` | `rrhh.evaluaciones.read` |
| `POST` | `/rrhh/trabajadores/{id}/evaluaciones/cualitativas` | `rrhh.evaluaciones.create` |

---

## Permisos RBAC

Total: **22 permisos** registrados en tabla `permissions` con `module = 'rrhh'`.

| Código | Descripción |
|--------|-------------|
| `rrhh.supervisores.read` | Ver supervisores |
| `rrhh.supervisores.create` | Crear supervisores |
| `rrhh.supervisores.update` | Editar supervisores |
| `rrhh.supervisores.delete` | Eliminar supervisores |
| `rrhh.tipos_permiso.read` | Ver tipos de permiso |
| `rrhh.tipos_permiso.create` | Crear tipos de permiso |
| `rrhh.tipos_permiso.update` | Editar tipos de permiso |
| `rrhh.trabajadores.read` | Ver trabajadores |
| `rrhh.trabajadores.create` | Crear trabajadores |
| `rrhh.trabajadores.update` | Editar trabajadores |
| `rrhh.trabajadores.delete` | Desactivar trabajadores |
| `rrhh.vacaciones.read` | Ver vacaciones |
| `rrhh.vacaciones.create` | Registrar vacaciones |
| `rrhh.vacaciones.update` | Editar vacaciones |
| `rrhh.vacaciones.delete` | Eliminar vacaciones |
| `rrhh.permisos.read` | Ver permisos laborales |
| `rrhh.permisos.create` | Registrar permisos laborales |
| `rrhh.permisos.update` | Editar permisos laborales |
| `rrhh.permisos.delete` | Eliminar permisos laborales |
| `rrhh.evaluaciones.read` | Ver evaluaciones |
| `rrhh.evaluaciones.create` | Crear evaluaciones |
| `rrhh.evaluaciones.update` | Editar evaluaciones |

---

## Reglas de negocio

- El `rut` y `codigo` son únicos por tenant — no se permiten duplicados.
- El trabajador no se elimina físicamente: se desactiva con `es_activo = false`.
- El cónyuge afiliado es único por trabajador (relación 1:1, upsert).
- Las cargas familiares tienen `fecha_vencimiento` — el sistema no las invalida automáticamente, debe gestionarse desde el cliente.
- Los relationships cross-módulo (`Afp`, `Isapre`, `Cargo`, `Sucursal`, `CentroCosto`, `Banco`, `Region`, `Comuna`) se omiten en los modelos SQLAlchemy para evitar conflictos de registry entre módulos. Las FK existen en BD; el acceso a esas tablas se hace mediante joins explícitos.

---

## Integración con Nómina

El módulo RRHH provee al motor de cálculo de nómina los siguientes datos del trabajador:

- Tasas previsionales (AFP, Isapre, modalidad)
- Cargas familiares activas (simples, invalidez, maternales)
- APV vigentes (monto y si rebaja base tributaria)
- Zona extrema (región y porcentaje DL 889)
- Tipo de contrato (indefinido vs plazo fijo → afecta Seguro Cesantía)
- Sueldo base, colación, movilización, gratificación
