# SaaS Base Platform — Manual Técnico para Desarrolladores

> **Stack:** FastAPI · PostgreSQL 16 · Docker · Vanilla JS  
> **Versión:** 1.0.0  
> **Última actualización:** 21/03/2026

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Infraestructura Docker](#2-infraestructura-docker)
3. [Variables de entorno](#3-variables-de-entorno)
4. [Arquitectura del backend](#4-arquitectura-del-backend)
5. [Base de datos](#5-base-de-datos)
6. [Frontend](#6-frontend)
7. [Seguridad](#7-seguridad)
8. [Agregar módulos nuevos](#8-agregar-módulos-nuevos)
9. [Errores comunes y soluciones](#9-errores-comunes-y-soluciones)
10. [Checklist antes de producción](#10-checklist-antes-de-producción)

---

## 1. Resumen ejecutivo

Esta base es una plataforma SaaS multi-tenant construida con FastAPI, PostgreSQL, Vanilla JS y Docker. Está diseñada para servir como fundación reutilizable de múltiples productos empresariales (remuneraciones, CRM, RRHH, contratos, etc.) sin necesidad de reescribir la infraestructura base para cada módulo nuevo.

> **Principio central:** Todo módulo nuevo hereda automáticamente autenticación, aislamiento de tenant, roles, auditoría y diseño visual. Solo se programa la lógica de negocio específica.

### Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend API | Python 3.12 + FastAPI 0.115 |
| Base de datos | PostgreSQL 16 (Alpine Docker image) |
| ORM / Migraciones | SQLAlchemy 2.0 + Alembic |
| Validación | Pydantic v2 + pydantic-settings |
| Autenticación | JWT (python-jose) + bcrypt (passlib 1.7.4 + bcrypt 4.0.1) |
| Frontend | HTML + CSS + JavaScript ES Modules (sin frameworks) |
| Servidor web | Nginx 1.27 (reverse proxy + archivos estáticos) |
| Contenedores | Docker + Docker Compose v2 |
| Admin BD | PgAdmin 4 |

---

## 2. Infraestructura Docker

### Servicios en ejecución

| Servicio | Puerto externo | Descripción |
|----------|---------------|-------------|
| `db` (postgres:16) | No expuesto | Base de datos. Solo accesible por red interna Docker `saas-net`. |
| `backend` (FastAPI) | No expuesto | API REST. Nginx actúa como proxy inverso. |
| `nginx` | `8085 → 80` | Sirve frontend estático + proxy `/api/` al backend. |
| `pgadmin` | `5050 → 80` | Interfaz web de administración de PostgreSQL. |

### Red interna Docker

Todos los servicios pertenecen a la red `saas-net` (bridge). Se comunican por nombre de servicio:

- `backend` conecta a la BD con: `postgresql://saas_user:saas_pass@db:5432/saas_db`
- `nginx` hace proxy a: `http://backend:8000`
- `pgadmin` conecta al host: `db`, puerto `5432`

> **Seguridad:** PostgreSQL NO está expuesto al exterior. Para acceso externo usar PgAdmin (puerto 5050) o SSH tunnel.

### Volúmenes persistentes

| Volumen | Descripción |
|---------|-------------|
| `postgres_data` | Datos de PostgreSQL. **NUNCA eliminar en producción.** |
| `pgadmin_data` | Configuración y conexiones guardadas de PgAdmin. |

### Comandos operacionales

#### Levantar y detener
```bash
docker compose up -d                    # levantar en background
docker compose down                     # detener (datos se conservan)
docker compose down -v                  # DESTRUCTIVO: elimina volúmenes
docker compose ps                       # ver estado de los servicios
```

#### Logs
```bash
docker compose logs -f backend          # logs del backend en tiempo real
docker compose logs -f                  # todos los servicios
docker compose logs --tail=50 backend   # últimas 50 líneas
```

#### Acceso a shells
```bash
docker compose exec backend bash        # shell en el contenedor backend
docker compose exec db psql -U saas_user -d saas_db   # psql directo
```

#### Migraciones
```bash
docker compose exec backend alembic upgrade head       # aplicar migraciones pendientes
docker compose exec backend alembic history            # ver historial de migraciones
docker compose exec backend alembic current            # versión actual aplicada
docker compose exec backend alembic downgrade -1       # revertir última migración
```

#### Reconstruir backend (tras cambios de código o dependencias)
```bash
docker compose build --no-cache backend
docker compose up -d backend
```

#### Makefile (shortcuts)
```bash
make up            # docker compose up -d
make down          # docker compose down
make logs          # logs del backend
make migrate       # alembic upgrade head
make shell-backend # bash en el backend
make shell-db      # psql directo
make secret        # generar SECRET_KEY
```

---

## 3. Variables de entorno

Todas las variables se definen en el archivo `.env` en la raíz del proyecto. El archivo `.env.example` contiene la plantilla. **NUNCA hacer commit del `.env` real a git.**

### Variables críticas de seguridad

> **CRÍTICO:** `SECRET_KEY` debe generarse con:
> ```bash
> python3 -c "import secrets; print(secrets.token_urlsafe(64))"
> ```
> Nunca usar el placeholder del `.env.example` en producción. Cambiar el `SECRET_KEY` invalida todas las sesiones activas.

| Variable | Valor de ejemplo | Descripción |
|----------|-----------------|-------------|
| `SECRET_KEY` | `kJ8mX2nP9q...` (64 chars) | Firma JWT. Cambiar invalida todas las sesiones. |
| `FIRST_SUPERADMIN_PASSWORD` | `Admin#2024Secure!` | Contraseña inicial. **Máx 72 caracteres.** Cambiar en primer login. |
| `DATABASE_URL` | `postgresql://user:pass@db/db` | Docker Compose la sobreescribe automáticamente. |

### Autenticación y sesiones

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | TTL del access token en cookie httpOnly. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | TTL del refresh token. Almacenado hasheado en BD. |
| `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` | `2` | TTL del enlace de recuperación de contraseña. |
| `ALGORITHM` | `HS256` | Algoritmo JWT. No cambiar sin migrar tokens existentes. |

### Email SMTP

> Para desarrollo usar [Mailtrap](https://mailtrap.io) (plan gratuito). Para producción usar SendGrid, Resend o Amazon SES.

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SMTP_HOST` | `sandbox.smtp.mailtrap.io` | Host del servidor SMTP. |
| `SMTP_PORT` | `587` | Puerto SMTP. 587 para STARTTLS, 465 para SSL. |
| `SMTP_TLS` | `true` | Activar STARTTLS. |
| `SMTP_USER` | `usuario_mailtrap` | Usuario SMTP. |
| `SMTP_PASSWORD` | `password_mailtrap` | Contraseña SMTP. |
| `EMAIL_FROM` | `noreply@tuapp.com` | Dirección remitente de todos los emails. |
| `FRONTEND_URL` | `http://tu-ip:8085` | URL base para enlaces en emails (reset password, etc.). |

### Rate limiting

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `LOGIN_RATE_LIMIT` | `10` | Intentos máximos de login por IP en la ventana de tiempo. |
| `LOGIN_RATE_WINDOW_SECONDS` | `300` | Ventana para rate limit de login (5 minutos). |
| `PASSWORD_RESET_RATE_LIMIT` | `3` | Intentos máximos de forgot-password por IP. |
| `PASSWORD_RESET_RATE_WINDOW_SECONDS` | `3600` | Ventana para rate limit de reset (1 hora). |

---

## 4. Arquitectura del backend

### Estructura de carpetas

```
backend/
├── app/
│   ├── main.py                  # FastAPI app + middleware + registro de routers
│   ├── core/
│   │   ├── config.py            # Settings centralizados (pydantic-settings)
│   │   └── security.py          # JWT, bcrypt, CSRF, política de contraseñas
│   ├── db/
│   │   └── session.py           # SQLAlchemy engine + get_db() dependency
│   ├── models/
│   │   └── models.py            # ORM: Tenant, User, RefreshToken, PasswordResetToken, AuditLog
│   ├── schemas/
│   │   └── schemas.py           # Pydantic schemas request/response
│   ├── auth/
│   │   ├── dependencies.py      # get_current_user, require_superadmin, require_tenant_access
│   │   └── rate_limit.py        # Rate limiting por IP (migrar a Redis en producción)
│   ├── api/v1/endpoints/
│   │   ├── auth.py              # login, logout, refresh, forgot/reset/change password, /me
│   │   ├── tenants.py           # CRUD tenants (solo superadmin)
│   │   └── users.py             # CRUD usuarios con cuota y tenant isolation
│   ├── email/
│   │   └── service.py           # Envío SMTP con templates HTML
│   ├── services/
│   │   └── audit.py             # Escritura en audit_logs
│   └── scripts/
│       └── bootstrap.py         # Crea primer superadmin al iniciar si no existe
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
├── alembic.ini
├── requirements.txt             # bcrypt==4.0.1  passlib[bcrypt]==1.7.4
└── Dockerfile
```

### Estrategia de autenticación

Se usa doble token con **cookies httpOnly**, no localStorage. XSS no puede leer cookies httpOnly.

| Elemento | Descripción |
|----------|-------------|
| `access_token` | httpOnly, Secure, SameSite=Lax. TTL: 30 min. Se envía en cada request. |
| `refresh_token` | httpOnly, Secure, SameSite=Strict. Path=/api/v1/auth/refresh. TTL: 7 días. |
| `csrf_token` | **NO** httpOnly. JS lo lee y lo envía en header `X-CSRF-Token` en mutaciones. |
| Refresh tokens en BD | Almacenados como SHA-256. Permiten revocación en logout y cambio de contraseña. |
| Rotación | Cada uso del refresh emite token nuevo e invalida el anterior (reuse detection). |

### Modelo multi-tenant

Estrategia: **Shared Database, Shared Schema** con `tenant_id` discriminator en todas las tablas.

- **Superadmin:** `tenant_id = NULL`. Acceso global a todos los tenants.
- **Admin:** `tenant_id` obligatorio. Solo gestiona usuarios de su propio tenant.
- **Viewer:** `tenant_id` obligatorio. Solo lectura dentro de su tenant.

> **Protección IDOR:** No está en los endpoints sino en las FastAPI dependencies (`dependencies.py`). `require_tenant_access()` valida el acceso antes de que corra cualquier lógica de negocio.

### Endpoints disponibles

#### Auth (`/api/v1/auth/`)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/login` | Login → set cookies httpOnly |
| POST | `/logout` | Logout → revocar tokens + limpiar cookies |
| POST | `/refresh` | Renovar access token usando refresh token |
| GET | `/me` | Usuario actual autenticado |
| POST | `/forgot-password` | Solicitar enlace de recuperación |
| POST | `/reset-password` | Resetear contraseña con token del email |
| POST | `/change-password` | Cambiar contraseña (autenticado) |

#### Tenants (`/api/v1/tenants/`) — solo superadmin
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Listar (paginado, búsqueda, filtro estado) |
| POST | `/` | Crear tenant |
| GET | `/{id}` | Detalle de un tenant |
| PATCH | `/{id}` | Actualizar tenant |
| PATCH | `/{id}/toggle-active` | Activar / desactivar tenant |

#### Usuarios (`/api/v1/users/`) — admin + superadmin
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Listar (scoped por tenant para admins) |
| POST | `/` | Crear usuario (valida cupo del tenant) |
| GET | `/{id}` | Detalle de usuario |
| PATCH | `/{id}` | Actualizar usuario |
| PATCH | `/{id}/toggle-active` | Activar / desactivar usuario |
| POST | `/{id}/reset-password` | Reset administrativo (envía contraseña temporal) |

---

## 5. Base de datos

### Tablas del sistema

| Tabla | Propósito | Notas |
|-------|-----------|-------|
| `tenants` | Organizaciones cliente. | `slug` único. `max_users` define el cupo. |
| `users` | Todos los usuarios del sistema. | `superadmin` tiene `tenant_id = NULL`. |
| `refresh_tokens` | Tokens de refresco activos por usuario. | Hasheados. `is_revoked` para invalidación. |
| `password_reset_tokens` | Tokens temporales de recuperación. | `is_used` previene reuso. TTL por `expires_at`. |
| `audit_logs` | Registro inmutable de eventos críticos. | **Nunca se modifica ni elimina.** Para SIEM futuro. |

### Campos clave en `users`

| Campo | Tipo | Propósito |
|-------|------|-----------|
| `force_password_change` | Boolean | Si `true`, frontend redirige a `/change-password` en el login. |
| `failed_login_attempts` | Integer | Contador de intentos fallidos. Base para account lockout futuro. |
| `locked_until` | DateTime | Timestamp de bloqueo (feature pendiente de implementar). |
| `last_login_ip` | String(45) | IP del último login. Para auditoría y detección de anomalías. |

### Agregar una nueva migración

```bash
# Dentro del contenedor backend, después de agregar/modificar un modelo:
docker compose exec backend alembic revision --autogenerate -m "descripcion_clara_del_cambio"
docker compose exec backend alembic upgrade head
```

> **Importante:** Revisar siempre el archivo generado en `alembic/versions/` antes de aplicar. Alembic no detecta renombrado de columnas ni cambios de tipo complejos de forma automática.

---

## 6. Frontend

### Páginas disponibles

| Archivo | Propósito |
|---------|-----------|
| `login.html` | Login. Verifica sesión activa y redirige si ya está autenticado. |
| `forgot-password.html` | Solicitar enlace de recuperación. Respuesta siempre neutral. |
| `reset-password.html` | Restablecer contraseña con token recibido por email. |
| `app.html` | Dashboard principal con sidebar y estadísticas. |
| `tenants.html` | CRUD completo de tenants (solo superadmin). |
| `users.html` | CRUD usuarios con filtros, cuota y aislamiento de tenant. |
| `change-password.html` | Cambio de contraseña autenticado. Soporta flujo forzado. |
| `settings.html` | Perfil de usuario, tema oscuro/claro, seguridad de cuenta. |

### Módulos JavaScript

| Archivo | Propósito |
|---------|-----------|
| `static/js/api.js` | HTTP client centralizado. Agrega CSRF automáticamente. Maneja refresh de sesión y redirige a login si expira. |
| `static/js/auth.js` | `requireAuth()`, `logout()`, `renderProfile()`. Guard de sesión para páginas protegidas. |
| `static/js/ui.js` | Modal, Panel deslizable, Paginación, Theme toggle, Profile menu, Confirm dialog. |
| `static/js/toast.js` | Notificaciones toast: `success`, `error`, `warning`, `info`. |
| `static/css/main.css` | Design system completo con variables CSS y soporte dark/light mode. |

### Cómo funciona `api.js`

Todos los `fetch` del frontend pasan por `api.js`, que se encarga de:

1. Leer el `csrf_token` de la cookie y enviarlo en `X-CSRF-Token` en mutaciones (POST, PATCH, DELETE).
2. Si recibe 401, intentar refresh automático una vez y reintentar el request original.
3. Si el refresh falla, redirigir a `/login.html`.
4. Normalizar errores con `{ message, status }` para manejo uniforme.

### Dark mode

El tema se guarda en `localStorage["theme"]` con valores `"light"` o `"dark"`. Se aplica mediante el atributo `data-theme` en el elemento `<html>`. El CSS usa variables CSS que cambian automáticamente:

```css
:root                  { --bg: #f8f9fc; --text-primary: #0f172a; }
[data-theme="dark"]    { --bg: #0a0f1e; --text-primary: #f1f5f9; }
```

---

## 7. Seguridad

### Controles implementados

| Amenaza | Control implementado |
|---------|---------------------|
| XSS (robo de tokens) | Access y refresh tokens en cookies `httpOnly`. JS no puede leerlos. |
| CSRF | Double-submit cookie pattern. `X-CSRF-Token` header requerido en mutaciones. |
| Brute force | Rate limiting por IP: 10 intentos/5min en login, 3/hora en reset password. |
| IDOR entre tenants | `tenant_id` validado en FastAPI dependencies, no en endpoints individuales. |
| Enumeración de usuarios | Forgot-password siempre responde igual, exista o no el email. |
| Session fixation | Refresh token rota en cada uso. Tokens nuevos en cada login. |
| Tokens de larga duración | Access token expira en 30 min. Revocación via tabla `refresh_tokens`. |
| Escalada de privilegios | Rol validado server-side en cada request vía FastAPI dependency. |
| Credenciales débiles | Mínimo 10 chars, mayúscula, minúscula, número, carácter especial. |
| Stack traces expuestos | Global exception handler devuelve solo mensaje genérico en producción. |
| Clickjacking | Header `X-Frame-Options: DENY` en todas las respuestas. |
| Inyección de contenido | Headers `CSP`, `X-Content-Type-Options: nosniff`. |

### Pendientes antes de producción real

- **Redis para rate limiting:** El store actual es en memoria y no funciona con múltiples instancias del backend.
- **Account lockout:** El campo `locked_until` ya existe en el modelo. Falta implementar la lógica de bloqueo.
- **MFA/TOTP:** Autenticación de dos factores con `pyotp` + QR code.
- **HTTPS obligatorio:** Configurar SSL en Nginx Proxy Manager con Let's Encrypt.
- **Secrets en vault:** Mover `SECRET_KEY` y credenciales a HashiCorp Vault o AWS Secrets Manager.
- **Rotación de SECRET_KEY:** Implementar proceso para rotar sin invalidar todas las sesiones simultáneamente.

---

## 8. Agregar módulos nuevos

Todo módulo nuevo sigue el mismo **patrón de 4 archivos**. No hay que modificar infraestructura, autenticación ni diseño visual. Solo se programa la lógica de negocio.

### El patrón completo (ejemplo: módulo Remuneraciones)

#### Paso 1 — Modelo en `models/models.py`

```python
class Liquidacion(Base):
    __tablename__ = "liquidaciones"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)  # SIEMPRE
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id"), nullable=False)
    mes           = Column(Integer, nullable=False)
    anio          = Column(Integer, nullable=False)
    sueldo_base   = Column(Numeric(12, 2), nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
```

#### Paso 2 — Schemas en `schemas/schemas.py`

```python
class LiquidacionCreate(BaseModel):
    trabajador_id: UUID
    mes: int
    anio: int
    sueldo_base: Decimal

class LiquidacionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    mes: int
    anio: int
    sueldo_base: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}
```

#### Paso 3 — Endpoint en `api/v1/endpoints/remuneraciones.py`

```python
router = APIRouter(prefix="/remuneraciones", tags=["remuneraciones"])

@router.get("/liquidaciones")
def listar(
    mes: int,
    anio: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    return db.query(Liquidacion).filter(
        Liquidacion.tenant_id == actor.tenant_id,  # aislamiento gratis
        Liquidacion.mes == mes,
        Liquidacion.anio == anio,
    ).all()

@router.post("/liquidaciones", status_code=201)
def crear(
    body: LiquidacionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin_or_superadmin),
):
    liq = Liquidacion(**body.model_dump(), tenant_id=actor.tenant_id)
    db.add(liq)
    db.commit()
    db.refresh(liq)
    log_event(db, "liquidacion.create", user_id=actor.id, tenant_id=actor.tenant_id)
    return liq
```

#### Paso 4 — Registrar en `main.py` (una línea)

```python
from app.api.v1.endpoints import remuneraciones
app.include_router(remuneraciones.router, prefix=settings.API_V1_STR)
```

#### Paso 5 — Migración

```bash
docker compose exec backend alembic revision --autogenerate -m "add_remuneraciones"
docker compose exec backend alembic upgrade head
```

#### Paso 6 — Frontend

Copiar `users.html` como base, cambiar los campos del formulario y apuntar los `fetch` a `/api/v1/remuneraciones`. Los archivos `api.js`, `ui.js`, `auth.js` y `main.css` no necesitan ninguna modificación.

---

### Lo que cada módulo hereda automáticamente

| Lo que se hereda | Cómo se activa |
|-----------------|----------------|
| Autenticación JWT completa | Declarar `Depends(get_current_user)` en el endpoint. |
| Aislamiento de tenant | Filtrar queries con `actor.tenant_id`. |
| Control de roles | Usar `Depends(require_admin_or_superadmin)` o `require_superadmin`. |
| Registro de auditoría | Llamar `log_event(db, "modulo.accion")` en operaciones críticas. |
| Protección CSRF | Automático en `api.js` para todas las mutaciones. Sin código adicional. |
| Design system visual | Incluir `main.css`. Todos los componentes ya están disponibles. |
| Refresh automático de sesión | Automático en `api.js`. Sin código adicional. |

### Arquitectura en capas

```
Base platform (ya construida)
└── Auth · Tenants · Users · RBAC · Audit · Docker

Servicios transversales (construir una vez)
└── Storage · PDF export · Background jobs · Webhooks · Email · Search

M�dulos de negocio (uno por uno, mismo patrón)
├── Remuneraciones    ← depende de: Trabajadores
├── CRM               ← depende de: Base únicamente
├── RRHH/Trabajadores ← depende de: Base únicamente  ← construir primero
├── Contratos         ← depende de: Trabajadores, Storage, PDF
├── Reclutamiento     ← depende de: Trabajadores
├── Rendiciones       ← depende de: Aprobaciones, Storage
├── Aprobaciones      ← depende de: Base (módulo transversal)
├── Documentos        ← depende de: Storage
└── Analytics/BI      ← depende de: todos los módulos (construir último)
```

### Secuencia de construcción recomendada

1. **Servicios transversales** — Storage de archivos, PDF export, Background jobs, Webhooks. Se construyen una vez y todos los módulos los usan.
2. **RRHH / Trabajadores** — Entidad central de la que dependen Remuneraciones, Contratos y Reclutamiento.
3. **Remuneraciones** — Mayor valor de negocio inmediato. Depende solo de Trabajadores.
4. **Aprobaciones / Workflows** — Módulo transversal. Construir cuando lo requiera Rendiciones o Contratos.
5. **CRM, Reclutamiento, Analytics** — Módulos más autónomos, sin bloquear la cadena de valor central.

---

## 9. Errores comunes y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `ValueError: password cannot be longer than 72 bytes` | `FIRST_SUPERADMIN_PASSWORD` demasiado largo. | Usar contraseña de menos de 72 caracteres en `.env`. |
| `AttributeError: module 'bcrypt' has no attribute '__about__'` | Incompatibilidad de `passlib` con versión nueva de `bcrypt`. | Fijar `bcrypt==4.0.1` y `passlib[bcrypt]==1.7.4` en `requirements.txt`. Rebuild con `--no-cache`. |
| `Port already allocated: 5432` | Otro PostgreSQL (local o contenedor) usando el puerto. | Eliminar el bloque `ports` del servicio `db` en `docker-compose.yml`. |
| `Port already allocated: 8000` o `8080` | Otro contenedor usando el puerto. | Eliminar exposición de puertos del `backend`. Nginx hace de proxy por red interna. |
| `Command 'python' not found` | Ubuntu/Debian usa `python3`, no `python`. | Reemplazar `python` por `python3` en `Makefile` y en el `command` del `docker-compose.yml`. |
| `CSRF validation failed 403` | Frontend no está enviando el header `X-CSRF-Token`. | Verificar que todas las mutaciones usan `api.js` (que lo agrega automáticamente). |
| `401` en refresh token | Refresh token expirado, revocado o inválido. | Normal. El usuario debe hacer login nuevamente. |
| `Alembic: target database is not up to date` | Hay migraciones pendientes sin aplicar. | `docker compose exec backend alembic upgrade head` |
| `Invalid hex value` en el arranque | Color con alpha (8 dígitos) en lugar de 6 dígitos hexadecimales. | Revisar variables de color en el código. Los colores deben ser 6 dígitos hex. |

---

## 10. Checklist antes de producción

### Configuración obligatoria

- [ ] **SECRET_KEY** generado con `secrets.token_urlsafe(64)`. Nunca el placeholder del `.env.example`.
- [ ] **Contraseña superadmin** cambiada en el primer login (`FIRST_SUPERADMIN_PASSWORD`).
- [ ] **`DEBUG=false`** y **`ENVIRONMENT=production`** en `.env`.
- [ ] **`ALLOWED_ORIGINS`** con solo el dominio real. Sin `localhost` ni wildcards.
- [ ] **SMTP real** configurado (SendGrid, Resend o Amazon SES). No Mailtrap.
- [ ] **`FRONTEND_URL`** apuntando a la URL pública real con HTTPS.

### Infraestructura obligatoria

- [ ] **HTTPS/SSL** configurado en Nginx Proxy Manager con certificado Let's Encrypt.
- [ ] **Backups automáticos** de PostgreSQL con `pg_dump` programado con cron.
- [ ] **Monitoreo** configurado: Sentry (errores), UptimeRobot (disponibilidad).
- [ ] **Firewall** con solo puertos 80, 443 y 22 expuestos al exterior.

### Mejoras de seguridad recomendadas

- [ ] **Redis** para rate limiting multi-instancia (reemplazar el store en memoria de `rate_limit.py`).
- [ ] **Account lockout** implementado usando el campo `locked_until` que ya existe en el modelo `users`.
- [ ] **MFA/TOTP** con `pyotp` + QR code para cuentas administrativas.
- [ ] **Rotación de SECRET_KEY** — proceso para rotar sin invalidar todas las sesiones simultáneamente.
- [ ] **Secrets en vault** — mover `SECRET_KEY` y credenciales a HashiCorp Vault o AWS Secrets Manager.

---

## Accesos por defecto (cambiar en primer uso)

| Servicio | URL | Credencial |
|----------|-----|-----------|
| Plataforma SaaS | `http://tu-ip:8085` | Email del `.env` + `FIRST_SUPERADMIN_PASSWORD` |
| PgAdmin | `http://tu-ip:5050` | `admin@admin.com` / `pgadmin_password` |
| PgAdmin → Servidor BD | host: `db`, port: `5432` | `saas_user` / `saas_pass` |

---

*SaaS Base Platform — Manual Técnico v1.0*