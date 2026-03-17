# Payroll Chile

SaaS multitenant de remuneraciones con FastAPI + PostgreSQL y frontend vanilla.

## Endurecimiento implementado
- Login multitenant con resolución por `tenant_code` (body), `X-Tenant-Code` o subdominio.
- JWT access token corto con claims: `sub=user_id`, `tid`, `sid`, `ver`, `iss`, `aud`, `iat`, `exp`.
- Refresh token rotativo en cookie `HttpOnly` (nunca en storage de frontend), guardando solo hash en DB.
- Patrón de frontend con access token en memoria y sin persistencia en navegador.
- Recuperación de contraseña con token aleatorio de un solo uso (hash en DB), respuesta uniforme.
- Cambio de contraseña autenticado con revocación de sesiones y aumento de `auth_version`.
- Argon2id como algoritmo principal + compatibilidad/rehash progresivo de hashes legacy.
- Auditoría dedicada (`backend/app/audit.py`) para eventos sensibles y bloqueos de rate limit.
- Rate limiting DB-backed por IP, tenant y email+tenant para login/forgot/reset.
- CORS restringido (`CORS_ALLOWED_ORIGINS`) y headers de seguridad en API y frontend nginx.

## Endpoints reales de autenticación
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout` (solo sesión actual)
- `POST /api/auth/logout-all` (todas las sesiones del usuario)
- `GET /api/auth/me`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `POST /api/auth/change-password`

## Aislamiento multitenant
- Búsqueda de usuario para autenticación siempre por `tenant_id + email_normalized`.
- Tokens de reset y sesiones validados con `tenant_id`.
- No hay uso cross-tenant de sesiones ni reset tokens.

## Variables `.env`
Usa `.env.example` y ajusta en producción:
- JWT y sesión: `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, `SESSION_IDLE_TIMEOUT_MINUTES`, `SESSION_ABSOLUTE_TIMEOUT_MINUTES`.
- Password reset/rate limit: `PASSWORD_RESET_TOKEN_MINUTES`, `PASSWORD_RESET_REQUESTS_PER_HOUR`, `LOGIN_MAX_ATTEMPTS`, `LOGIN_WINDOW_MINUTES`.
- Seguridad: `PASSWORD_MIN_LENGTH`, `BLOCKLIST_PATH`, `CORS_ALLOWED_ORIGINS`.
- Cookies: `COOKIE_SECURE`, `COOKIE_SAMESITE`, `COOKIE_DOMAIN`.
- SMTP: `ENABLE_PASSWORD_RECOVERY`, `SMTP_*`, `APP_BASE_URL`.

## Frontend y headers
`frontend/nginx.conf` agrega:
- `Content-Security-Policy`
- `Permissions-Policy`
- `Referrer-Policy`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Cache-Control: no-store` para vistas sensibles (`app/change-password/forgot-password/reset-password`).

> HSTS: como este nginx de frontend no termina TLS, `Strict-Transport-Security` debe aplicarse en el reverse proxy TLS perimetral (por ejemplo ingress, ALB/CloudFront, nginx/traefik externo).

## Ejecutar
```bash
cp .env.example .env
docker compose up --build
```

## Tests
```bash
cd backend
pytest -q
```
