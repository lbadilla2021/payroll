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

Se crea/actualiza automáticamente un superadmin al iniciar el backend:

- Email: `SUPERADMIN_EMAIL` (por defecto `superadmin@payroll.local`)
- Password: `SUPERADMIN_PASSWORD` (por defecto `admin123`)

## Migraciones

Las migraciones SQL se ejecutan al inicio desde `backend/migrations/*.sql`.

## Si aparece `HTTP 502` al autenticar

Generalmente indica que el backend no está sano todavía.

```bash
docker compose ps
docker compose logs -f backend frontend
```

Si cambiaste credenciales y tienes volumen viejo de Postgres, vuelve a levantar para que el init script reconcilie el superadmin con el `.env` actual.
