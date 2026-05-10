# Sistema de Remuneraciones Chile — SaaS Multi-Tenant

Plataforma de liquidaciones de sueldo para Chile, construida como SaaS B2B multi-tenant.  
Implementa la legislación laboral vigente: Código del Trabajo, DL 3.500, Ley 19.728, DFL-1.

**Stack:** FastAPI · PostgreSQL 16 · Vanilla JS · Docker · Nginx · Redis

---

## Arranque rápido

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env: SECRET_KEY, SMTP_*, FIRST_SUPERADMIN_EMAIL, FIRST_SUPERADMIN_PASSWORD

# 2. Levantar servicios
make up
# (equivalente a: docker compose up -d)

# 3. Verificar estado
make status
docker compose logs backend --tail=30

# 4. Aplicar migraciones y crear superadmin
make migrate
make bootstrap

# 5. Abrir en el navegador
open http://localhost:8085

# Login inicial con las credenciales definidas en FIRST_SUPERADMIN_* del .env
```

---

## Servicios

| Servicio   | Puerto externo | Descripción                          |
|------------|----------------|--------------------------------------|
| **nginx**  | 8085           | Frontend + reverse proxy API         |
| **backend**| 8000 (interno) | FastAPI (solo acceso interno)        |
| **db**     | 5432 (interno) | PostgreSQL 16                        |
| **redis**  | 6379 (interno) | Rate limiting y caché de sesiones    |
| **pgadmin**| 5050           | Administrador web de base de datos   |

---

## Comandos Make

```bash
make secret         # Genera un SECRET_KEY seguro
make up             # Levanta todos los servicios
make down           # Detiene los servicios (preserva volúmenes)
make logs           # Sigue los logs del backend en tiempo real
make migrate        # Aplica migraciones Alembic (upgrade head)
make bootstrap      # Crea el primer superadmin (idempotente)
make shell-backend  # Abre bash en el contenedor backend
make shell-db       # Abre psql en el contenedor de base de datos
make status         # Estado de los contenedores
make reset-db       # ⚠ DESTRUCTIVO: elimina volúmenes y recrea todo
```

---

## Estructura del proyecto

```
payroll/
├── .env                          # Variables de entorno (no commitear)
├── .env.example                  # Plantilla de variables
├── docker-compose.yml            # Orquestación multi-contenedor
├── Makefile                      # Atajos de comandos
├── docker/
│   └── nginx.conf                # Reverse proxy + servidor de archivos estáticos
├── documentacion/
│   ├── 01_autenticacion.md       # Sistema de auth, JWT, sesiones, middleware
│   ├── 02_modulo_rrhh.md         # Módulo RRHH, trabajadores, evaluaciones, permisos
│   └── 03_modulo_nomina.md       # Módulo Nómina, motor de cálculo, contratos, finiquitos
├── backend/
│   ├── app/
│   │   ├── main.py               # Entrypoint FastAPI + middleware stack
│   │   ├── core/
│   │   │   ├── config.py         # Settings con pydantic-settings
│   │   │   └── security.py       # JWT, bcrypt, CSRF, política de contraseñas
│   │   ├── db/session.py         # Engine SQLAlchemy + get_db()
│   │   ├── models/models.py      # ORM: Tenant, User, RefreshToken, RBAC, AuditLog
│   │   ├── schemas/schemas.py    # Schemas Pydantic request/response
│   │   ├── auth/
│   │   │   ├── dependencies.py   # Dependencies FastAPI (auth, authz, tenant isolation)
│   │   │   └── rate_limit.py     # Rate limiting por IP (en memoria)
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py           # login, logout, refresh, forgot/reset/change-password
│   │   │   ├── tenants.py        # CRUD tenants (superadmin)
│   │   │   ├── users.py          # CRUD usuarios (admin + superadmin)
│   │   │   ├── roles.py          # Gestión de roles
│   │   │   ├── permissions.py    # Consulta de permisos
│   │   │   ├── groups.py         # Grupos de usuarios
│   │   │   └── invitations.py    # Invitaciones por token
│   │   ├── email/service.py      # SMTP con templates HTML
│   │   ├── services/audit.py     # Registro en audit_logs
│   │   └── scripts/bootstrap.py # Crea primer superadmin al iniciar
│   ├── modulos/
│   │   ├── rrhh/
│   │   │   ├── models.py         # ORM schema rrhh: Trabajador, CargaFamiliar, Evaluaciones...
│   │   │   ├── endpoints.py      # ~100 rutas RRHH
│   │   │   ├── services.py       # Lógica de negocio RRHH
│   │   │   ├── repositories.py   # Acceso a datos RRHH
│   │   │   └── permissions.py    # 58 permisos RBAC del módulo RRHH
│   │   └── nomina/
│   │       ├── models.py         # ORM schema nomina: 35+ tablas
│   │       ├── endpoints.py      # ~80 rutas catálogos nómina
│   │       ├── endpoints_operacional.py  # ~30 rutas operacionales
│   │       ├── services.py / services_operacional.py
│   │       ├── repositories.py / repositories_operacional.py
│   │       ├── permissions.py    # 58 permisos RBAC del módulo Nómina
│   │       └── calculo/
│   │           ├── motor.py      # Motor de cálculo (17 pasos, puro, sin efectos)
│   │           ├── servicio_calculo.py   # Orquestación: DB → motor → persistencia
│   │           ├── schemas_calculo.py    # Estructuras de entrada/salida del cálculo
│   │           └── endpoints_calculo.py # 3 rutas: individual, masivo, reportes
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial_schema.py   # Plataforma base (tenants, users, tokens, audit)
│   │       ├── 0002_invitation_tokens.py
│   │       ├── 0003_rbac.py             # Roles, permisos, RBAC
│   │       ├── 0004_groups_and_system_roles.py
│   │       ├── 0005_modulo_nomina.py    # Schema nomina: 35+ tablas
│   │       ├── 0006_modulo_rrhh.py      # Schema rrhh: 20+ tablas
│   │       ├── 0007_rrhh_mantenedores.py
│   │       └── 0008_seg_cesantia_movimiento.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── login.html / forgot-password.html / reset-password.html
│   ├── change-password.html / accept-invitation.html
│   ├── app.html                  # Dashboard principal
│   ├── tenants.html / users.html / roles.html / groups.html / settings.html
│   ├── rrhh/
│   │   ├── trabajadores.html     # Nómina de trabajadores
│   │   ├── trabajador.html       # Ficha completa del trabajador
│   │   ├── catalogos.html        # Supervisores, tipos de permiso, evaluaciones
│   │   └── mantenedores.html
│   ├── nomina/
│   │   ├── catalogos.html        # AFP, Isapres, bancos, regiones, comunas, monedas
│   │   ├── empresa.html          # Configuración de la empresa
│   │   ├── parametros.html       # Parámetros mensuales (UTM, UF, IMM)
│   │   ├── contratos.html        # Contratos de trabajo
│   │   ├── movimientos.html      # Movimientos de nómina
│   │   ├── calculo.html          # Motor de cálculo de remuneraciones
│   │   ├── carga-masiva.html     # Carga masiva de movimientos
│   │   ├── finiquitos.html       # Finiquitos y liquidaciones de contrato
│   │   ├── prestamos.html        # Préstamos a trabajadores
│   │   └── anticipos.html        # Anticipos de sueldo
│   └── static/
│       ├── css/main.css          # Design system completo (variables CSS, dark/light mode)
│       └── js/
│           ├── api.js            # HTTP client: CSRF, refresh automático, redirect
│           ├── auth.js           # requireAuth(), logout(), renderProfile()
│           ├── auth-guard.js     # Verificación de sesión antes de cargar la página
│           ├── ui.js             # Modal, Panel deslizable, Paginación, Toggle de tema
│           ├── toast.js          # Notificaciones (success, error, warning, info)
│           └── nav.js            # Sidebar dinámico según permisos del usuario
└── scripts/                      # Scripts de utilidad
```

---

## Motor de cálculo de remuneraciones

El motor (`backend/modulos/nomina/calculo/motor.py`) es un componente puro (sin efectos laterales) que implementa el algoritmo de liquidación chilena en 17 pasos:

| Paso | Concepto | Legislación |
|------|----------|-------------|
| 1 | Sueldo base proporcional (días trabajados) | CT Art. 55 |
| 2 | Horas extras (1.5x normal · 2.0x nocturna/festivo) | CT Art. 32 |
| 3 | Colación y movilización (no imponibles) | CT Art. 42 |
| 4 | Gratificación (25% imponible, tope 4.75 IMM) | CT Art. 50 |
| 5 | Otros haberes (fijos y variables) | — |
| 6 | Total imponible (base de cálculo previsional) | DL 3.500 |
| 7 | AFP + SIS (tasa Previred + 1.49%, tope 81.6 UF) | DL 3.500 |
| 8 | Seguro de Cesantía (0.6% trabajador / 2.4-3.0% empleador) | Ley 19.728 |
| 9 | Salud (7% FONASA o plan Isapre con diferencia) | DFL-1 |
| 10 | APV voluntario (con opción rebaja Art. 42 BIS) | Ley 20.255 |
| 11 | Base imponible tributaria | DFL-1 Art. 42 |
| 12 | Asignación de zona extrema (Regiones I, XI, XII, XV) | DL 889 |
| 13 | Impuesto Único 2ª categoría (tramos en UTM) | DFL-1 |
| 14 | Asignación familiar (por tramo de renta, no tributable) | DFL-1 |
| 15 | Descuentos varios (préstamos, anticipos, otros) | — |
| 16 | Líquido a pagar | — |
| 17 | Resumen de carga del empleador | — |

**Conceptos previsionales soportados:**

| Entidad | Rol |
|---------|-----|
| AFP | Pensiones (tasa variable por AFP, cargada desde tabla Previred) |
| Isapre / FONASA | Salud (plan con cobertura o 7% mínimo legal) |
| CCAF | Administración de asignación familiar y bienestar |
| Mutualidad | Seguro de accidentes del trabajo (cargo empleador) |
| Seguro de Cesantía | AFC según tipo de contrato |

---

## Base de datos

**Estrategia multi-tenant:** Base compartida con `tenant_id` como discriminador. Row-Level Security activado vía `SET app.current_tenant_id` en cada sesión de base de datos.

### Schemas

| Schema | Tablas | Descripción |
|--------|--------|-------------|
| `public` | ~12 | Plataforma: tenants, users, tokens, RBAC, audit_logs |
| `rrhh` | ~20 | RRHH: trabajadores, cargas familiares, permisos, préstamos, evaluaciones |
| `nomina` | ~35 | Nómina: catálogos, movimientos, contratos, finiquitos, cálculo |

### Tablas clave (módulo nómina)

**Catálogos globales** (sin `tenant_id`, compartidos entre tenants):
- `afp`, `isapre`, `ccaf`, `mutualidad` — Entidades previsionales
- `banco`, `tipo_movimiento_bancario` — Medios de pago
- `region`, `comuna` — Divisiones administrativas de Chile (16 regiones, 276+ comunas)
- `tramo_asignacion_familiar` — Tramos de asignación familiar por año/mes
- `tramo_impuesto_unico_utm` — Tramos del Impuesto Único en UTM
- `factor_actualizacion` — Índices mensuales UTM, UF, IMM

**Tablas operacionales** (con `tenant_id`):
- `movimiento_mensual` + `movimiento_concepto` — Cabecera + líneas de liquidación
- `contrato` + `contrato_clausula` — Contratos de trabajo
- `finiquito` + `finiquito_concepto` — Finiquitos
- `prestamo` + `prestamo_cuota` — Préstamos con cuotas
- `anticipo` — Anticipos de sueldo
- `certificado_impuesto` — Certificado de renta anual (DJ 1887)
- `parametro_mensual` — Período contable (UTM/UF del mes, estado bloqueado/cerrado)

---

## API Reference

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login → setea cookies httpOnly |
| POST | `/api/v1/auth/logout` | Logout → revoca token en BD |
| POST | `/api/v1/auth/refresh` | Renueva access token con rotación |
| GET  | `/api/v1/auth/me` | Usuario autenticado actual |
| POST | `/api/v1/auth/forgot-password` | Solicitar reset por email |
| POST | `/api/v1/auth/reset-password` | Resetear con token de email |
| POST | `/api/v1/auth/change-password` | Cambiar contraseña (autenticado) |

### Tenants (solo superadmin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/v1/tenants` | Listar (paginado + búsqueda) |
| POST   | `/api/v1/tenants` | Crear tenant |
| GET    | `/api/v1/tenants/{id}` | Detalle |
| PATCH  | `/api/v1/tenants/{id}` | Actualizar |
| PATCH  | `/api/v1/tenants/{id}/toggle-active` | Activar/desactivar |

### Usuarios
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/v1/users` | Listar (scoped por tenant) |
| POST   | `/api/v1/users` | Crear usuario |
| GET    | `/api/v1/users/{id}` | Detalle |
| PATCH  | `/api/v1/users/{id}` | Actualizar |
| PATCH  | `/api/v1/users/{id}/toggle-active` | Activar/desactivar |
| POST   | `/api/v1/users/{id}/reset-password` | Reset administrativo |

### RRHH (`/api/v1/rrhh/`)
Gestión de trabajadores, cargas familiares, permisos, vacaciones, préstamos, evaluaciones, supervisores y catálogos de RRHH. ~100 rutas con control RBAC granular (58 permisos).

### Nómina (`/api/v1/nomina/`)
Catálogos previsionales, parámetros mensuales, movimientos, contratos, finiquitos, préstamos, anticipos y generación LRE. ~110 rutas con control RBAC granular (58 permisos).

### Cálculo (`/api/v1/nomina/calculo/`)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/nomina/calculo/calcular` | Calcular liquidación individual |
| POST | `/api/v1/nomina/calculo/calcular-masivo` | Cálculo batch de todo el período |
| GET  | `/api/v1/nomina/calculo/reporte/{periodo}` | Reporte del período calculado |

---

## Seguridad implementada

| Control | Implementación |
|---------|----------------|
| **Contraseñas** | bcrypt cost 12 — nunca en texto plano |
| **Sesiones** | Cookie httpOnly (access 30 min) + refresh token hasheado en BD (7 días) |
| **CSRF** | Double-submit cookie: `csrf_token` no-httpOnly enviado en `X-CSRF-Token` |
| **Rate limiting** | Login 10/5 min · Password reset 3/1 hr (por IP, en memoria) |
| **Anti-enumeración** | Forgot-password responde igual independiente de si el email existe |
| **IDOR** | `tenant_id` validado en dependency FastAPI, no en cada endpoint |
| **Headers HTTP** | `X-Frame-Options DENY` · `nosniff` · CSP · `Referrer-Policy` |
| **Audit log** | Toda operación crítica registrada en `audit_logs` (inmutable) |
| **Revocación** | Logout y cambio de contraseña invalidan refresh tokens en BD |
| **Tenant inactivo** | Login rechazado si el tenant está desactivado |
| **Separación de datos** | Row-Level Security por `tenant_id` a nivel de sesión de BD |

---

## Variables de entorno críticas

| Variable | Descripción | En producción |
|----------|-------------|---------------|
| `SECRET_KEY` | Firma JWT | `secrets.token_urlsafe(64)` en vault |
| `DATABASE_URL` | Conexión PostgreSQL | URL con SSL habilitado |
| `SMTP_*` | Servidor de correo | Proveedor transaccional (SES, SendGrid, Postmark) |
| `ALLOWED_ORIGINS` | CORS whitelist | Dominio exacto (sin wildcards) |
| `ENVIRONMENT` | Modo de operación | `production` |
| `DEBUG` | Logs detallados | `false` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL del access token | 30 (ajustar según política) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | TTL del refresh token | 7 |

---

## Checklist antes de producción

- [ ] `SECRET_KEY` generado con `make secret` y almacenado en vault (no en `.env`)
- [ ] `FIRST_SUPERADMIN_PASSWORD` cambiado inmediatamente después del primer login
- [ ] `DEBUG=false` y `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` con dominio real (sin `localhost`)
- [ ] HTTPS configurado en nginx (certificado SSL + redirect 80 → 443)
- [ ] PostgreSQL con usuario de mínimos privilegios (sin superuser)
- [ ] Backups automáticos de BD configurados y probados
- [ ] SMTP con proveedor transaccional verificado
- [ ] Rate limiting migrado a Redis (para despliegue multi-instancia)
- [ ] Rotación de logs configurada
- [ ] Monitoreo y alertas configurados (Sentry, Datadog, etc.)
- [ ] Revisión de catálogos previsionales: tasas AFP, tramos UF/UTM actualizados al período

---

## Roadmap

### P0 — Producción inmediata
- Redis para rate limiting multi-instancia (actualmente en memoria del proceso)
- SSL/HTTPS en nginx con Let's Encrypt o certificado corporativo
- Gestión de secretos con Vault o AWS Secrets Manager
- Backup automatizado de PostgreSQL (pg_dump + S3 o similar)

### P1 — Seguridad
- MFA/TOTP (pyotp + código QR)
- Account lockout tras N intentos fallidos (campo existe en BD, falta lógica)
- Blacklist de tokens en Redis para revocación instantánea
- Rotación automática de SECRET_KEY

### P2 — Nómina avanzada
- Generación de archivo LRE (Libro de Remuneraciones Electrónico) para el SII
- Generación de DJ 1887 (certificado de renta anual)
- Colilla de liquidación en PDF (WeasyPrint o reportlab)
- Previred: exportación de nómina previsional
- Carga masiva de movimientos desde CSV/Excel

### P3 — Operaciones RRHH
- Flujo de aprobación de finiquitos
- Gestión de ausencias y control de asistencia
- Contrato digital con firma electrónica
- Portal de autoservicio para trabajadores

### P4 — Enterprise y plataforma
- SSO/SAML/OIDC (Authlib)
- API keys para integraciones M2M
- Webhooks por eventos (nómina.calculada, contrato.firmado, etc.)
- Multi-idioma (i18n)
- Módulo de reportería avanzada (Power BI / Looker embed)
