# Payroll Chile

SaaS multitenant de remuneraciones con FastAPI + PostgreSQL y frontend vanilla.

## Seguridad implementada
- Login multitenant con `tenant_code` (o resolución por host/header), sin búsquedas ambiguas por email.
- JWT access token corto con claims: `sub=user_id`, `tid`, `sid`, `ver`, `iss`, `aud`, `iat`, `exp`.
- Refresh token rotativo en cookie `HttpOnly` (`Secure` configurable por entorno), guardando solo hash en DB.
- Recuperación de contraseña por email con token aleatorio de un solo uso (hash en DB).
- Cambio de contraseña autenticado + revocación de sesiones + incremento de `auth_version`.
- Argon2id como hash principal y rehash progresivo para hashes legacy.
- Auditoría en `auth_audit_logs` y rate limiting por IP/email/tenant.
- CORS restringido por `CORS_ALLOWED_ORIGINS` y headers de seguridad.

## Variables `.env`
Usa `.env.example` como plantilla. Variables clave:
- Sesión: `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, `SESSION_IDLE_TIMEOUT_MINUTES`, `SESSION_ABSOLUTE_TIMEOUT_MINUTES`.
- Password reset: `PASSWORD_RESET_TOKEN_MINUTES`, `PASSWORD_RESET_REQUESTS_PER_HOUR`, `ENABLE_PASSWORD_RECOVERY`, `SMTP_*`.
- Seguridad: `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `PASSWORD_MIN_LENGTH`, `CORS_ALLOWED_ORIGINS`.
- Cookies: `COOKIE_SECURE`, `COOKIE_SAMESITE`, `COOKIE_DOMAIN`.

## Flujos
- Login: `POST /api/auth/login`
- Refresh: `POST /api/auth/refresh`
- Logout: `POST /api/auth/logout`, `POST /api/auth/logout-all`
- Perfil: `GET /api/auth/me`
- Forgot password: `POST /api/auth/forgot-password`
- Reset password: `POST /api/auth/reset-password`
- Change password: `POST /api/auth/change-password`

## Aislamiento de tenants
- Usuarios se identifican por `tenant_id + email_normalized`.
- Tokens, sesiones y resets se validan contra `tenant_id`.
- No hay reutilización cross-tenant de tokens de reset ni de sesiones.

## Producción
1. Configura `ENVIRONMENT=production`.
2. Usa `JWT_SECRET` robusto y `SUPERADMIN_PASSWORD` no default.
3. Define `CORS_ALLOWED_ORIGINS` explícito (nunca `*`).
4. Activa `COOKIE_SECURE=true` detrás de HTTPS.
5. Configura SMTP real y monitoreo de auditoría/rate-limit.
