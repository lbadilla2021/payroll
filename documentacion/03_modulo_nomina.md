# Módulo Nómina

## Descripción general

El módulo Nómina gestiona el proceso completo de remuneraciones para empresas chilenas, desde la configuración de catálogos hasta el cálculo de liquidaciones con plena conformidad a la legislación laboral vigente.

**Stack:** FastAPI · SQLAlchemy · PostgreSQL (schema `nomina`) · RLS por tenant

---

## Estructura de archivos

```
modulos/nomina/
├── models.py                    ← Modelos SQLAlchemy (schema nomina.*)
├── schemas.py                   ← Schemas Pydantic catálogos + operacionales iter.2
├── schemas_operacional.py       ← Schemas Pydantic operacionales iter.3
├── repositories.py              ← Repos catálogos y operacionales iter.2
├── repositories_operacional.py  ← Repos operacionales iter.3
├── services.py                  ← Servicios iter.2
├── services_operacional.py      ← Servicios iter.3
├── endpoints.py                 ← Router principal (~80 rutas iter.2)
├── endpoints_operacional.py     ← Rutas operacionales iter.3 (~30 rutas)
├── permissions.py               ← 58 permisos RBAC + seed
├── schema.sql                   ← DDL de referencia
└── calculo/
    ├── motor.py                 ← Algoritmos puros (sin BD)
    ├── servicio_calculo.py      ← Orquestador BD → motor → persistencia
    ├── schemas_calculo.py       ← Schemas de entrada/salida del cálculo
    └── endpoints_calculo.py     ← 3 rutas del motor
```

---

## Base de datos

### Catálogos globales (sin `tenant_id`)

Datos compartidos entre todos los tenants. Solo superadmin puede modificarlos.

| Tabla | Descripción | Registros seed |
|-------|-------------|----------------|
| `nomina.afp` | AFP vigentes con tasas Previred | 10 AFP |
| `nomina.isapre` | Isapres y Fonasa | 10 Isapres |
| `nomina.ccaf` | Cajas de Compensación | 5 CCAF |
| `nomina.mutualidad` | Mutualidades de seguridad | 4 Mutualidades |
| `nomina.banco` | Bancos (Tabla N°2 Transtecnia) | 26 Bancos |
| `nomina.tipo_movimiento_bancario` | Tipos mov. bancario (Tabla N°3) | 8 tipos |
| `nomina.region` | Regiones de Chile | 16 regiones |
| `nomina.comuna` | Comunas de Chile | Representativas |
| `nomina.tipo_moneda` | Monedas (CLP, UF, UTM, USD, EUR) | 5 monedas |
| `nomina.tramo_asignacion_familiar` | Tramos AF por año/mes | 2024 cargado |
| `nomina.tramo_impuesto_unico_utm` | Tabla IU en UTM por año/mes | 2024 cargado |
| `nomina.factor_actualizacion` | UTM, UF, IMM por período | — |
| `nomina.serv_med_cchc` | Parámetros Serv. Méd. CCHC | — |

### Tablas operacionales por tenant (con RLS)

| Tabla | Descripción |
|-------|-------------|
| `nomina.empresa_config` | Configuración tributaria/previsional de la empresa |
| `nomina.sucursal` | Sucursales de la empresa |
| `nomina.centro_costo` | Centros de costo |
| `nomina.cargo` | Cargos configurables |
| `nomina.tipo_contrato` | Tipos de contrato |
| `nomina.causal_finiquito` | Causales de finiquito (Art. CT) |
| `nomina.clausula_adicional` | Cláusulas adicionales de contratos |
| `nomina.concepto_remuneracion` | Haberes (H) y descuentos (D) configurables |
| `nomina.parametro_mensual` | UTM/UF/IMM/topes por empresa y período |
| `nomina.movimiento_mensual` | Cabecera del proceso mensual por trabajador |
| `nomina.movimiento_concepto` | Haberes/descuentos del movimiento mensual |
| `nomina.contrato` | Contratos de trabajo |
| `nomina.contrato_clausula` | Cláusulas asociadas a contratos |
| `nomina.finiquito` | Finiquitos de trabajadores |
| `nomina.finiquito_concepto` | Conceptos del finiquito |
| `nomina.prestamo` | Préstamos a trabajadores |
| `nomina.prestamo_cuota` | Cuotas individuales de préstamos |
| `nomina.anticipo` | Anticipos de remuneraciones |
| `nomina.certificado_impuesto` | Certificado anual retenciones / DJ 1887 |
| `nomina.retencion_anual` | Retenciones 3% Ley 21.252 |
| `nomina.lre_generacion` | Registro de generaciones LRE |

---

## API — Endpoints

Todas las rutas tienen prefijo `/api/v1`.

### Catálogos Globales (lectura libre para autenticados)

#### AFP
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/catalogos/afp` | Autenticado |
| `GET` | `/nomina/catalogos/afp/{id}` | Autenticado |
| `PATCH` | `/nomina/catalogos/afp/{id}` | Solo superadmin |

#### Isapres
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/catalogos/isapres` | Autenticado |
| `GET` | `/nomina/catalogos/isapres/{id}` | Autenticado |
| `PATCH` | `/nomina/catalogos/isapres/{id}` | Solo superadmin |

#### CCAF y Mutualidades
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/catalogos/ccaf` | Autenticado |
| `GET` | `/nomina/catalogos/ccaf/{id}` | Autenticado |
| `GET` | `/nomina/catalogos/mutualidades` | Autenticado |
| `GET` | `/nomina/catalogos/mutualidades/{id}` | Autenticado |

#### Bancos y Movimientos Bancarios
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/catalogos/bancos` | Autenticado |
| `GET` | `/nomina/catalogos/movimientos-bancarios` | Autenticado |

#### Geografía
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/catalogos/regiones` | Autenticado |
| `GET` | `/nomina/catalogos/regiones/{id}/comunas` | Autenticado |
| `GET` | `/nomina/catalogos/comunas` | Autenticado |

#### Monedas
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/catalogos/monedas` | Autenticado |

### Parámetros Tributarios (escritura solo superadmin)

#### Asignación Familiar
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/parametros/asignacion-familiar/vigente` | Autenticado |
| `GET` | `/nomina/parametros/asignacion-familiar/{anio}/{mes}` | Autenticado |
| `PUT` | `/nomina/parametros/asignacion-familiar/{anio}/{mes}` | Solo superadmin |

#### Impuesto Único
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/parametros/impuesto-unico/vigente` | Autenticado |
| `GET` | `/nomina/parametros/impuesto-unico/{anio}/{mes}` | Autenticado |
| `PUT` | `/nomina/parametros/impuesto-unico/{anio}/{mes}` | Solo superadmin |

#### Factores UTM/UF/IMM
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/parametros/factores` | Autenticado |
| `GET` | `/nomina/parametros/factores/vigente` | Autenticado |
| `POST` | `/nomina/parametros/factores` | Solo superadmin |
| `PATCH` | `/nomina/parametros/factores/{anio}/{mes}` | Solo superadmin |

#### Serv. Médico CCHC
| Método | Ruta | Acceso |
|--------|------|--------|
| `GET` | `/nomina/parametros/serv-med-cchc/vigente` | Autenticado |
| `POST` | `/nomina/parametros/serv-med-cchc` | Solo superadmin |
| `PATCH` | `/nomina/parametros/serv-med-cchc/{anio}/{mes}` | Solo superadmin |

### Operacionales Tenant-scoped

#### Empresa Config
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/empresa` | `nomina.empresa.read` |
| `PUT` | `/nomina/empresa` | `nomina.empresa.update` |
| `PATCH` | `/nomina/empresa` | `nomina.empresa.update` |

#### Sucursales
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/sucursales` | `nomina.sucursales.read` |
| `POST` | `/nomina/sucursales` | `nomina.sucursales.create` |
| `GET` | `/nomina/sucursales/{id}` | `nomina.sucursales.read` |
| `PATCH` | `/nomina/sucursales/{id}` | `nomina.sucursales.update` |
| `DELETE` | `/nomina/sucursales/{id}` | `nomina.sucursales.delete` |

#### Centros de Costo
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/centros-costo` | `nomina.centros_costo.read` |
| `POST` | `/nomina/centros-costo` | `nomina.centros_costo.create` |
| `GET` | `/nomina/centros-costo/{id}` | `nomina.centros_costo.read` |
| `PATCH` | `/nomina/centros-costo/{id}` | `nomina.centros_costo.update` |
| `DELETE` | `/nomina/centros-costo/{id}` | `nomina.centros_costo.delete` |

#### Cargos
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/cargos` | `nomina.cargos.read` |
| `POST` | `/nomina/cargos` | `nomina.cargos.create` |
| `GET` | `/nomina/cargos/{id}` | `nomina.cargos.read` |
| `PATCH` | `/nomina/cargos/{id}` | `nomina.cargos.update` |
| `DELETE` | `/nomina/cargos/{id}` | `nomina.cargos.delete` |

#### Tipos de Contrato
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/tipos-contrato` | `nomina.tipos_contrato.read` |
| `POST` | `/nomina/tipos-contrato` | `nomina.tipos_contrato.create` |
| `PATCH` | `/nomina/tipos-contrato/{id}` | `nomina.tipos_contrato.update` |
| `DELETE` | `/nomina/tipos-contrato/{id}` | `nomina.tipos_contrato.delete` |

#### Causales de Finiquito
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/causales-finiquito` | `nomina.causales_finiquito.read` |
| `POST` | `/nomina/causales-finiquito` | `nomina.causales_finiquito.create` |
| `PATCH` | `/nomina/causales-finiquito/{id}` | `nomina.causales_finiquito.update` |
| `DELETE` | `/nomina/causales-finiquito/{id}` | `nomina.causales_finiquito.delete` |

#### Cláusulas Adicionales
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/clausulas-adicionales` | `nomina.clausulas.read` |
| `POST` | `/nomina/clausulas-adicionales` | `nomina.clausulas.create` |
| `PATCH` | `/nomina/clausulas-adicionales/{id}` | `nomina.clausulas.update` |
| `DELETE` | `/nomina/clausulas-adicionales/{id}` | `nomina.clausulas.delete` |

#### Conceptos de Remuneración (Haberes y Descuentos)
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/conceptos` | `nomina.conceptos.read` |
| `POST` | `/nomina/conceptos` | `nomina.conceptos.create` |
| `GET` | `/nomina/conceptos/{id}` | `nomina.conceptos.read` |
| `PATCH` | `/nomina/conceptos/{id}` | `nomina.conceptos.update` |
| `DELETE` | `/nomina/conceptos/{id}` | `nomina.conceptos.delete` |

**Filtros disponibles:** `tipo` (H/D), `search`, `solo_activos`

#### Parámetros Mensuales (por empresa)
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/parametros-mensuales` | `nomina.parametros.read` |
| `GET` | `/nomina/parametros-mensuales/vigente` | `nomina.parametros.read` |
| `POST` | `/nomina/parametros-mensuales` | `nomina.parametros.create` |
| `GET` | `/nomina/parametros-mensuales/{anio}/{mes}` | `nomina.parametros.read` |
| `PATCH` | `/nomina/parametros-mensuales/{anio}/{mes}` | `nomina.parametros.update` |

#### Contratos de Trabajo
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/contratos` | `nomina.contratos.read` |
| `POST` | `/nomina/contratos` | `nomina.contratos.create` |
| `GET` | `/nomina/contratos/{id}` | `nomina.contratos.read` |
| `PATCH` | `/nomina/contratos/{id}` | `nomina.contratos.update` |
| `PATCH` | `/nomina/contratos/{id}/finalizar` | `nomina.contratos.update` |

#### Movimientos Mensuales
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/movimientos` | `nomina.movimientos.read` |
| `POST` | `/nomina/movimientos` | `nomina.movimientos.create` |
| `GET` | `/nomina/movimientos/resumen/{anio}/{mes}` | `nomina.movimientos.read` |
| `GET` | `/nomina/movimientos/trabajador/{id}/{anio}/{mes}` | `nomina.movimientos.read` |
| `GET` | `/nomina/movimientos/{id}` | `nomina.movimientos.read` |
| `PATCH` | `/nomina/movimientos/{id}` | `nomina.movimientos.update` |
| `DELETE` | `/nomina/movimientos/{id}` | `nomina.movimientos.delete` |
| `GET` | `/nomina/movimientos/{id}/conceptos` | `nomina.movimientos.read` |
| `POST` | `/nomina/movimientos/{id}/conceptos` | `nomina.movimientos.update` |
| `PATCH` | `/nomina/movimientos/{id}/conceptos/{concepto_id}` | `nomina.movimientos.update` |
| `DELETE` | `/nomina/movimientos/{id}/conceptos/{concepto_id}` | `nomina.movimientos.update` |

#### Finiquitos
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/finiquitos` | `nomina.finiquitos.read` |
| `POST` | `/nomina/finiquitos` | `nomina.finiquitos.create` |
| `GET` | `/nomina/finiquitos/{id}` | `nomina.finiquitos.read` |
| `PATCH` | `/nomina/finiquitos/{id}` | `nomina.finiquitos.update` |
| `GET` | `/nomina/finiquitos/{id}/conceptos` | `nomina.finiquitos.read` |
| `POST` | `/nomina/finiquitos/{id}/conceptos` | `nomina.finiquitos.update` |
| `DELETE` | `/nomina/finiquitos/{id}/conceptos/{concepto_id}` | `nomina.finiquitos.update` |

#### Préstamos
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/prestamos` | `nomina.prestamos.read` |
| `POST` | `/nomina/prestamos` | `nomina.prestamos.create` |
| `GET` | `/nomina/prestamos/{id}` | `nomina.prestamos.read` |
| `GET` | `/nomina/prestamos/{id}/cuotas` | `nomina.prestamos.read` |
| `PATCH` | `/nomina/prestamos/{id}/cuotas/{cuota_id}` | `nomina.prestamos.update` |
| `POST` | `/nomina/prestamos/{id}/pago-anticipado` | `nomina.prestamos.update` |
| `PATCH` | `/nomina/prestamos/{id}/cancelar` | `nomina.prestamos.delete` |

#### Anticipos
| Método | Ruta | Permiso |
|--------|------|---------|
| `GET` | `/nomina/anticipos` | `nomina.anticipos.read` |
| `POST` | `/nomina/anticipos` | `nomina.anticipos.create` |
| `GET` | `/nomina/anticipos/resumen/{trabajador_id}/{anio}/{mes}` | `nomina.anticipos.read` |
| `GET` | `/nomina/anticipos/{id}` | `nomina.anticipos.read` |
| `PATCH` | `/nomina/anticipos/{id}` | `nomina.anticipos.update` |
| `PATCH` | `/nomina/anticipos/{id}/anular` | `nomina.anticipos.delete` |

### Motor de Cálculo

| Método | Ruta | Permiso |
|--------|------|---------|
| `POST` | `/nomina/calculo/movimiento/{id}` | `nomina.calculo.ejecutar` |
| `POST` | `/nomina/calculo/empresa` | `nomina.calculo.ejecutar` |
| `GET` | `/nomina/calculo/movimiento/{id}/preview` | `nomina.calculo.ejecutar` |

---

## Motor de Cálculo — Detalle

### Arquitectura

```
BD (trabajador, AFP, isapre, cargas, APV, parámetros)
    ↓
servicio_calculo.py   ← orquestador: carga datos, construye estructuras
    ↓
motor.py              ← algoritmos puros, stateless, sin BD
    ↓
ResultadoCalculo      ← dataclass con todos los montos
    ↓
MovimientoMensual     ← persistencia de resultados
```

El `motor.py` es **completamente independiente de la BD** y puede testearse de forma unitaria con valores conocidos.

### Proceso de cálculo (orden legislativo)

| Paso | Concepto | Referencia legal |
|------|----------|-----------------|
| 1 | Sueldo base proporcional a días trabajados | Art. 55 CT |
| 2 | Horas extras (×1.5 normales, ×2.0 nocturnas/festivas) | Art. 32 CT |
| 3 | Colación y movilización (exentas de imposiciones y tributo) | Art. 41 CT |
| 4 | Gratificación 25% con tope 4.75 IMM | Art. 50 CT |
| 5 | Haberes adicionales del movimiento (imponibles/no imponibles) | — |
| 6 | **Total imponible** (base cotizaciones previsionales) | DL 3.500 |
| 7 | Cotización AFP con tope 81.6 UF | DL 3.500 |
| 8 | SIS — Seguro Invalidez y Sobrevivencia (cargo empleador) | DL 3.500 |
| 9 | Cotización salud 7% tope 60 UF + diferencia Isapre (6 modalidades) | Ley 18.933 |
| 10 | Seguro de Cesantía (trabajador indefinido 0.6% / plazo fijo solo empleador 3%) | Ley 19.728 |
| 11 | APV rebaja base tributaria según Art. 42 BIS | Ley de la Renta |
| 12 | **Base impuesto único** (imponible − cotizaciones − APV) | Art. 42 Nº1 LIR |
| 13 | Rebaja zona extrema DL 889 (regiones I, XI, XII, XV) | DL 889 |
| 14 | Impuesto único tabla UTM progresiva | Art. 43 LIR |
| 15 | Asignación familiar por tramos (simple, invalidez, maternal) | DFL-150 |
| 16 | Descuentos varios y préstamos | — |
| 17 | **Líquido a pagar** | — |

### Isapre — 6 modalidades soportadas

| Modalidad | Descripción |
|-----------|-------------|
| 1 | Monto fijo en pesos |
| 2 | Monto fijo en UF |
| 3 | Solo 7% legal (sin diferencia) |
| 4 | 7% + adicional en UF |
| 5 | 7% + adicional en UF + pesos |
| 6 | Pesos + UF |

### Cálculo masivo por empresa

`POST /nomina/calculo/empresa` procesa todos los movimientos con estado `pendiente` o `calculado` del período. Los errores individuales no detienen el proceso — se acumulan en `detalle_errores` y el resto continúa.

---

## Permisos RBAC

Total: **58 permisos** registrados en tabla `permissions` con `module = 'nomina'`.

### Operacionales (requieren permiso de tenant)

| Grupo | Permisos |
|-------|----------|
| Empresa config | `nomina.empresa.read`, `nomina.empresa.update` |
| Sucursales | `.read` `.create` `.update` `.delete` |
| Centros de costo | `.read` `.create` `.update` `.delete` |
| Cargos | `.read` `.create` `.update` `.delete` |
| Tipos de contrato | `.read` `.create` `.update` `.delete` |
| Causales de finiquito | `.read` `.create` `.update` `.delete` |
| Cláusulas adicionales | `.read` `.create` `.update` `.delete` |
| Conceptos remuneración | `.read` `.create` `.update` `.delete` |
| Parámetros mensuales | `.read` `.create` `.update` |
| Contratos | `.read` `.create` `.update` `.delete` |
| Movimientos | `.read` `.create` `.update` `.delete` |
| Finiquitos | `.read` `.create` `.update` `.delete` |
| Préstamos | `.read` `.create` `.update` `.delete` |
| Anticipos | `.read` `.create` `.update` `.delete` |
| Motor de cálculo | `nomina.calculo.ejecutar` |

### Catálogos globales

Los catálogos globales (AFP, isapres, bancos, regiones, etc.) **no requieren permiso de tenant** — cualquier usuario autenticado puede leerlos. La modificación de tasas/tramos/factores requiere rol `superadmin`.

---

## Reglas de negocio

### Contratos
- No se puede crear un segundo contrato vigente para el mismo trabajador sin finalizar el anterior.
- El contrato se finaliza con `PATCH /contratos/{id}/finalizar` que cambia estado a `finiquitado`.

### Movimientos mensuales
- Bloqueados si el período tiene `bloqueado = true` o `cerrado = true` en `parametro_mensual`.
- No se pueden eliminar movimientos en estado `cerrado`.
- Un trabajador puede tener múltiples movimientos en un mismo mes (`nro_movimiento` 1, 2, 3...) para casos de finiquito + recontratación.

### Finiquitos
- Solo se puede firmar (cambiar estado a `firmado`) si tiene causal asignada y al menos un concepto.
- No se puede modificar un finiquito en estado `pagado`.
- El `total_finiquito` se recalcula automáticamente al agregar/eliminar conceptos.

### Préstamos
- Las cuotas se generan automáticamente al crear el préstamo.
- El `saldo_pendiente` se recalcula automáticamente al marcar cuotas como pagadas.
- El préstamo pasa a estado `cancelado` cuando `saldo_pendiente = 0`.

### Anticipos
- Validación de período no bloqueado al crear.
- No se puede modificar el monto de un anticipo `procesado`.
- No se puede anular un anticipo `procesado` (requiere nota de crédito).

### Parámetros mensuales
- Un período bloqueado no permite modificaciones salvo el desbloqueo explícito.
- Un período cerrado no permite ninguna modificación.

---

## Migraciones Alembic

| Revisión | Descripción |
|----------|-------------|
| `0005` | Schema `nomina.*`: 33 tablas + RLS + seeds catálogos |
| `0006` | Schema `rrhh.*`: 19 tablas + RLS |

Las migraciones son **idempotentes** — verifican existencia de tablas e índices antes de crearlos, y usan `ON CONFLICT DO NOTHING` en los seeds. Son seguras de ejecutar sobre una BD con tablas ya existentes.

```bash
# Aplicar migraciones
docker compose stop backend
docker compose run --rm backend alembic upgrade head
docker compose start backend
```
