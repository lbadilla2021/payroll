# Payroll Chile (base mínima)

Proyecto mínimo dockerizado para gestión multitenant con:

- Backend: Python + FastAPI + PostgreSQL
- Frontend: HTML + CSS + JavaScript vanilla
- Autenticación JWT
- Superadmin con panel para crear tenants y usuarios por tenant

## Estructura

- `backend/`: API y migraciones SQL.
- `frontend/`: login y panel principal.

## Levantar el entorno

```bash
cp .env.example .env
docker compose up --build
```

Aplicación en `http://localhost:8080`.

## Credenciales iniciales

Se crea automáticamente un superadmin al iniciar el backend:

- Email: `SUPERADMIN_EMAIL` (por defecto `superadmin@payroll.local`)
- Password: `SUPERADMIN_PASSWORD` (por defecto `admin123`)

## Migraciones

Las migraciones SQL se ejecutan al inicio desde `backend/migrations/*.sql`.
