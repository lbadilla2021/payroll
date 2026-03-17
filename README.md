# Payroll Chile

Base FastAPI + PostgreSQL + frontend vanilla para payroll multitenant con seguridad reforzada.

## Cambios de seguridad implementados

- Login tenant-aware (`tenant_code`, header `X-Tenant-Code` o subdominio).
- Sesiones robustas: access token corto + refresh token rotativo en cookie `HttpOnly`.
- Expiración por inactividad y expiración absoluta de sesión configurables.
- Recuperación de contraseña con token de un solo uso almacenado como hash.
- Cambio de contraseña autenticado con invalidación de sesiones activas.
- Auditoría de eventos críticos (`auth_audit_logs`).
- Rate limiting en login y forgot password por IP/cuenta/tenant.
- Endurecimiento de CORS (no abierto por defecto).
- Multi-tenant isolation por diseño (`users` único por `(tenant_id,email)`).

## Variables de entorno

Ver `.env.example` para configuración completa:
- Tokens/sesión: `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, `SESSION_IDLE_TIMEOUT_MINUTES`, `SESSION_ABSOLUTE_TIMEOUT_DAYS`.
- Password reset: `PASSWORD_RESET_TOKEN_MINUTES`, `PASSWORD_RESET_REQUESTS_PER_HOUR`.
- Login throttling: `LOGIN_MAX_ATTEMPTS`, `LOGIN_WINDOW_MINUTES`.
- Password policy: `PASSWORD_MIN_LENGTH`, `BLOCKLIST_PATH`.
- SMTP: `SMTP_*` y `APP_BASE_URL`.
- Cookies: `COOKIE_SECURE`, `COOKIE_SAMESITE`, `COOKIE_DOMAIN`.
- CORS: `CORS_ALLOWED_ORIGINS`.

## Flujos

- `/` login
- `/forgot-password.html` solicitar reset
- `/reset-password.html?token=...` reset
- `/change-password.html` cambio autenticado

## Ejecutar

```bash
cp .env.example .env
docker compose up --build
```
