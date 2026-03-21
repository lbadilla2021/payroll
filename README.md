# SaaS Base Platform

Base arquitectónica multi-tenant para sistemas empresariales B2B.
Stack: FastAPI · PostgreSQL · Vanilla JS · Docker

---

## Arranque rápido (5 pasos)

```bash
# 1. Clonar y configurar variables
cp .env.example .env
# Editar .env: SECRET_KEY, SMTP_*, FIRST_SUPERADMIN_PASSWORD

# 2. Levantar servicios
docker compose up -d

# 3. Verificar que todo esté corriendo
docker compose ps
docker compose logs backend --tail=30

# 4. Abrir en el navegador
open http://localhost:8080

# 5. Login inicial
#    Email:    admin@platform.com  (o el que definiste en .env)
#    Password: ChangeMe!2024#SuperSecret
#    ⚠ El sistema te forzará a cambiar la contraseña al primer login
```

---

## Servicios

| Servicio  | Puerto | Descripción                     |
|-----------|--------|---------------------------------|
| nginx     | 8080   | Frontend + proxy API            |
| backend   | 8000   | FastAPI (solo en dev)           |
| db        | 5432   | PostgreSQL 16                   |

---

## Estructura del proyecto

```
saas-base/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entrypoint FastAPI + middleware
│   │   ├── core/
│   │   │   ├── config.py            # Settings (pydantic-settings)
│   │   │   └── security.py         # JWT, bcrypt, CSRF, password policy
│   │   ├── db/session.py            # SQLAlchemy engine + get_db()
│   │   ├── models/models.py         # ORM: Tenant, User, RefreshToken...
│   │   ├── schemas/schemas.py       # Pydantic request/response schemas
│   │   ├── auth/
│   │   │   ├── dependencies.py     # FastAPI dependencies de auth/authz
│   │   │   └── rate_limit.py       # Rate limiting por IP
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py              # login, logout, refresh, pwd flows
│   │   │   ├── tenants.py           # CRUD tenants (superadmin)
│   │   │   └── users.py             # CRUD usuarios (admin+superadmin)
│   │   ├── email/service.py         # SMTP con templates HTML
│   │   ├── services/audit.py        # Escritura de audit_logs
│   │   └── scripts/bootstrap.py    # Crea primer superadmin
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial_schema.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── login.html
│   ├── forgot-password.html
│   ├── reset-password.html
│   ├── app.html                     # Dashboard principal
│   ├── tenants.html                 # CRUD tenants
│   ├── users.html                   # CRUD usuarios
│   ├── change-password.html
│   ├── settings.html
│   └── static/
│       ├── css/main.css             # Design system completo
│       └── js/
│           ├── api.js               # HTTP client + CSRF + refresh
│           ├── auth.js              # requireAuth(), logout(), renderProfile()
│           ├── ui.js                # Modal, Panel, Toast, Pagination, Theme
│           └── toast.js             # Notificaciones
├── docker/nginx.conf
├── docker-compose.yml
└── .env.example
```

---

## Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f backend

# Ejecutar migraciones manualmente
docker compose exec backend alembic upgrade head

# Acceder a psql
docker compose exec db psql -U saas_user -d saas_db

# Verificar tablas
docker compose exec db psql -U saas_user -d saas_db -c "\dt"

# Re-crear superadmin si se pierde
docker compose exec backend python -m app.scripts.bootstrap

# Abrir shell en backend
docker compose exec backend bash

# Detener todo y limpiar volúmenes (DESTRUCTIVO)
docker compose down -v
```

---

## API Reference (endpoints principales)

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login → set cookies |
| POST | `/api/v1/auth/logout` | Logout → revoke + clear cookies |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET  | `/api/v1/auth/me` | Usuario actual |
| POST | `/api/v1/auth/forgot-password` | Solicitar reset |
| POST | `/api/v1/auth/reset-password` | Resetear con token |
| POST | `/api/v1/auth/change-password` | Cambiar (autenticado) |

### Tenants (superadmin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/v1/tenants` | Listar (paginado, busqueda) |
| POST   | `/api/v1/tenants` | Crear |
| GET    | `/api/v1/tenants/{id}` | Detalle |
| PATCH  | `/api/v1/tenants/{id}` | Actualizar |
| PATCH  | `/api/v1/tenants/{id}/toggle-active` | Activar/desactivar |

### Usuarios (admin + superadmin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/v1/users` | Listar (scoped por tenant) |
| POST   | `/api/v1/users` | Crear (valida cupo) |
| GET    | `/api/v1/users/{id}` | Detalle |
| PATCH  | `/api/v1/users/{id}` | Actualizar |
| PATCH  | `/api/v1/users/{id}/toggle-active` | Activar/desactivar |
| POST   | `/api/v1/users/{id}/reset-password` | Reset admin |

---

## Seguridad implementada

- **Passwords**: bcrypt cost 12 — nunca almacenados en texto plano
- **Sesiones**: httpOnly cookie (access 30min) + refresh token hasheado en BD (7 días)
- **CSRF**: Double-submit cookie pattern en todas las mutaciones
- **Rate limiting**: Login 10/5min · Password reset 3/1hr (por IP)
- **Enumeración**: Forgot password siempre responde igual independiente del email
- **IDOR**: tenant_id validado en cada dependency FastAPI, no a nivel de endpoint
- **Headers**: X-Frame-Options DENY · nosniff · CSP · Referrer-Policy
- **Audit**: Toda operación crítica escribe en audit_logs
- **Tokens revocados**: Logout y cambio de contraseña invalidan refresh tokens en BD
- **Tenant inactivo**: Login rechazado si el tenant está inactivo

---

## Variables de entorno críticas

| Variable | Descripción | Valor en producción |
|----------|-------------|---------------------|
| `SECRET_KEY` | Firma JWT | `secrets.token_urlsafe(64)` |
| `DATABASE_URL` | Conexión PostgreSQL | URL completa con SSL |
| `SMTP_*` | Servidor de correo | Proveedor transaccional |
| `ALLOWED_ORIGINS` | CORS whitelist | Tu dominio exacto |
| `ENVIRONMENT` | Modo | `production` |
| `DEBUG` | Logs detallados | `false` |

---

## Antes de producción — checklist

- [ ] `SECRET_KEY` generado con `secrets.token_urlsafe(64)` y guardado en vault
- [ ] `FIRST_SUPERADMIN_PASSWORD` cambiado en el primer login
- [ ] `DEBUG=false` y `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` con dominio real (sin localhost)
- [ ] HTTPS configurado en nginx (certificado SSL + redirect 80→443)
- [ ] PostgreSQL con usuario de mínimos privilegios (no superuser)
- [ ] Backups automáticos de BD
- [ ] SMTP con proveedor transaccional (SendGrid, Postmark, SES)
- [ ] Rate limiting migrado a Redis (para múltiples instancias)
- [ ] Rotación de logs configurada
- [ ] Monitoreo/alertas configurados (Sentry, Datadog, etc.)

---

## Roadmap de mejoras prioritarias

### P0 — Producción inmediata
- Redis para rate limiting multi-instancia
- SSL/HTTPS en nginx con Let's Encrypt
- Gestión de secretos con Vault o AWS Secrets Manager
- Backup automatizado de PostgreSQL

### P1 — Seguridad
- MFA/TOTP (pyotp + QR code)
- Account lockout tras N intentos fallidos
- Blacklist de tokens en Redis (revocación instantánea)
- Rotación automática de SECRET_KEY

### P2 — Funcionalidad
- RBAC granular (tabla `permissions`, no solo roles)
- Módulo de configuración por tenant (JSONB `settings`)
- Vista de audit log en frontend (filtrable, exportable)
- Invitaciones por email (usuario activa su propia cuenta)

### P3 — Enterprise
- SSO/SAML/OIDC (python-saml, Authlib)
- API keys para integraciones M2M
- Webhooks por eventos (tenant.created, user.login, etc.)
- Multi-idioma (i18n)

### P4 — Módulos de negocio
Añadir sobre esta base:
- `remuneraciones/` — liquidaciones, colillas, imposiciones
- `contratos/` — plantillas, firma digital
- `crm/` — contactos, oportunidades, pipeline
- `documentos/` — gestión documental con versionado
- `aprobaciones/` — flujos de aprobación configurables
