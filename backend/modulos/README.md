# Módulos: RRHH y Nómina

## Estructura de archivos

```
modulos/
├── __init__.py
├── rrhh/
│   ├── __init__.py
│   ├── models.py       ← Modelos SQLAlchemy (schema rrhh.*)
│   └── schema.sql      ← DDL completo con RLS y seeds
└── nomina/
    ├── __init__.py
    ├── models.py       ← Modelos SQLAlchemy (schema nomina.*)
    └── schema.sql      ← DDL completo con RLS y seeds
```

---

## Separación de responsabilidades

| Módulo | Qué contiene | Qué NO contiene |
|--------|-------------|-----------------|
| **rrhh** | Datos personales del trabajador, datos laborales (sueldo base, forma pago, previsión), cargas familiares, APV, vacaciones, permisos, préstamos (vista RRHH), evaluaciones, cargos desempeñados | Conceptos de remuneración, cálculo de liquidaciones, tablas tributarias |
| **nomina** | AFP, isapres, CCAF, mutualidades, bancos, comunas, tramos tributarios, UTM/UF, conceptos haberes/descuentos, movimiento mensual, contratos, finiquitos, préstamos (descuento nómina), anticipo, LRE | Datos biográficos del trabajador |

---

## Multi-tenancy y RLS

### Estrategia elegida
Shared database, shared schema con `tenant_id` en todas las tablas operacionales.
RLS habilitado vía `SET app.current_tenant_id = '<uuid>'` antes de cada operación.

### Tablas SIN tenant_id (catálogos globales)
Son datos que no varían por empresa. Se cargan como seed al iniciar el sistema:

- `nomina.afp` — AFP y tasas vigentes
- `nomina.isapre` — Isapres y Fonasa
- `nomina.ccaf` — Cajas de compensación
- `nomina.mutualidad` — Mutualidades de seguridad
- `nomina.banco` — Tabla bancos (Tabla N°2 Transtecnia)
- `nomina.tipo_movimiento_bancario` — Tabla N°3 Transtecnia
- `nomina.region` / `nomina.comuna` — División política Chile
- `nomina.tipo_moneda` — CLP, UF, UTM, USD, EUR
- `nomina.tramo_asignacion_familiar` — Se actualiza anualmente (DT)
- `nomina.tramo_impuesto_unico_utm` — Se actualiza anualmente (SII)
- `nomina.factor_actualizacion` — UTM/UF/IMM mensuales
- `rrhh.tipo_permiso_global` — Tipos de permiso base
- `rrhh.tipo_cargo_rrhh_global` — Tipos de cargo base

### Tablas CON tenant_id (operacionales con RLS)
Todas las demás tablas en ambos módulos.

### Configurar RLS en la sesión
```python
# En el middleware/dependency FastAPI
async def set_tenant(db: AsyncSession, tenant_id: str):
    await db.execute(
        text("SET LOCAL app.current_tenant_id = :tid"),
        {"tid": tenant_id}
    )
```

---

## Seeds incluidos en schema.sql

| Tabla | Registros seed |
|-------|---------------|
| `nomina.afp` | 10 (Capital, Cuprum, Habitat, Modelo, Planvital, ProVida, Uno, IPS, EMPART, SSS) |
| `nomina.isapre` | 10 (Fonasa + 9 Isapres vigentes) |
| `nomina.ccaf` | 5 (Los Andes, Los Héroes, La Araucana, 18 Sept., Gabriela Mistral) |
| `nomina.mutualidad` | 4 (ACHS, IST, Mutual CCHC, IPS/INS) |
| `nomina.banco` | 26 (según Tabla N°2 manual Transtecnia cap. 9.7.2) |
| `nomina.tipo_movimiento_bancario` | 8 (según Tabla N°3 manual Transtecnia) |
| `nomina.region` | 16 regiones (incluyendo flag zona extrema) |
| `nomina.comuna` | Extracto representativo (cargar CSV completo en prod) |
| `nomina.tipo_moneda` | 5 (CLP, UF, UTM, USD, EUR) |
| `nomina.tramo_asignacion_familiar` | 4 tramos 2024 (actualizar anualmente) |
| `nomina.tramo_impuesto_unico_utm` | 8 tramos 2024 (actualizar anualmente) |
| `rrhh.tipo_permiso_global` | 7 tipos base |

---

## Tablas vacías (por diseño)

Según instrucción: si el manual menciona la entidad pero no lista datos explícitos,
la tabla se crea sin seed. Ejemplos:

- `nomina.causal_finiquito` — Por tenant; seed opcional vía bootstrap script
- `nomina.tipo_contrato` — Por tenant (indefinido, plazo fijo, obra/faena)
- `nomina.concepto_remuneracion` — Haberes/descuentos propios de cada empresa
- `nomina.parametro_mensual` — Se llena en proceso de cierre mensual
- `nomina.serv_med_cchc` — Se ingresa manualmente o vía actualización DT
- Todas las tablas de fichas RRHH — Se llenan por operación del sistema

---

## Orden de aplicación DDL

```bash
# 1. Proyecto base (public schema — ya existe)
# psql < backend/alembic/versions/0001_initial_schema.py  (via alembic)

# 2. Schema nómina (catálogos primero, luego operacionales)
psql -d payroll_db < modulos/nomina/schema.sql

# 3. Schema RRHH (depende de nomina para FK a region, comuna, cargo, etc.)
psql -d payroll_db < modulos/rrhh/schema.sql
```

---

## Integración con Alembic

Para integrar con el sistema de migraciones existente, crear:

```
backend/alembic/versions/0005_modulo_nomina.py
backend/alembic/versions/0006_modulo_rrhh.py
```

Importar los modelos en `alembic/env.py`:
```python
import modulos.nomina.models  # noqa
import modulos.rrhh.models    # noqa
```

---

## Referencias al manual Transtecnia

| Sección manual | Tablas resultantes |
|---------------|-------------------|
| Cap. 4.1 Creación Empresa | `nomina.empresa_config` |
| Cap. 4.3 UTM/Factores | `nomina.factor_actualizacion` |
| Cap. 4.4.1 Datos Personales | `rrhh.trabajador` (campos personales) |
| Cap. 4.4.2 Datos Laborales | `rrhh.trabajador` (campos laborales) |
| Cap. 4.4.3 Datos Previsionales | `rrhh.trabajador` (campos prev.) + `rrhh.trabajador_apv` + `rrhh.trabajador_conyuge_afiliado` |
| Cap. 4.4.4 Cargas Familiares | `rrhh.carga_familiar` + `rrhh.carga_familiar_sueldo_mensual` |
| Cap. 4.5 Centros de Costo | `nomina.centro_costo` |
| Cap. 4.6 Cargos | `nomina.cargo` |
| Cap. 4.7 Haberes y Descuentos | `nomina.concepto_remuneracion` |
| Cap. 4.8 Tipos de Contratos | `nomina.tipo_contrato` |
| Cap. 4.9 Causales Finiquito | `nomina.causal_finiquito` |
| Cap. 4.10 Cláusulas Adicionales | `nomina.clausula_adicional` |
| Cap. 4.11.2 Tipos de Moneda | `nomina.tipo_moneda` |
| Cap. 4.12 Sucursales | `nomina.sucursal` |
| Cap. 5.1.1 Parámetros | `nomina.parametro_mensual` |
| Cap. 5.1.2 Cargas Familiares | `nomina.tramo_asignacion_familiar` |
| Cap. 5.1.3/4 Imp. Único | `nomina.tramo_impuesto_unico_utm` |
| Cap. 5.1.5 Serv. Med. CCHC | `nomina.serv_med_cchc` |
| Cap. 5.2 Movimiento Mensual | `nomina.movimiento_mensual` + `nomina.movimiento_concepto` |
| Cap. 5.4 Contratos | `nomina.contrato` + `nomina.contrato_clausula` |
| Cap. 5.5 Finiquitos | `nomina.finiquito` + `nomina.finiquito_concepto` |
| Cap. 6.4/7.6 Anticipos | `nomina.anticipo` |
| Cap. 6.5 Certificados Imp. | `nomina.certificado_impuesto` |
| Cap. 6.5.6/7 Retenciones 3% | `nomina.retencion_anual` |
| Cap. 7.22 LRE | `nomina.lre_generacion` |
| Cap. 8.1 Supervisores | `rrhh.supervisor` |
| Cap. 8.2 Tipos Permisos | `rrhh.tipo_permiso` |
| Cap. 8.3.1/8.9 Vacaciones | `rrhh.ficha_vacacion` |
| Cap. 8.3.2 Permisos | `rrhh.ficha_permiso` |
| Cap. 8.3.3 Préstamos RRHH | `rrhh.ficha_prestamo` |
| Cap. 8.3.4 Cargos Desempeñados | `rrhh.cargo_desempenado` |
| Cap. 8.3.5 Observaciones | `rrhh.observacion` |
| Cap. 8.3.7/8.4 Eval. Cuantit. | `rrhh.trabajador_eval_cuantitativa` + catálogos |
| Cap. 8.3.8/8.7 Eval. Cualit. | `rrhh.trabajador_eval_cualitativa` + catálogos |
| Cap. 8.3.9 Contratos RRHH | `rrhh.contrato_rrhh` |
| Cap. 8.10 Préstamos Nómina | `nomina.prestamo` + `nomina.prestamo_cuota` |
| Tab. N°1 Comunas | `nomina.comuna` (276 comunas) |
| Tab. N°2 Bancos | `nomina.banco` (26 bancos) |
| Tab. N°3 Mov. Bancario | `nomina.tipo_movimiento_bancario` (8 tipos) |
