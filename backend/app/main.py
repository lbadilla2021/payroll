"""
Application entrypoint.

Security middleware stack (applied in reverse order of declaration):
1. TrustedHost — reject requests with invalid Host headers
2. CORS — allow only configured origins
3. Security headers — X-Frame-Options, CSP, etc.
4. GZip — for larger responses
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import auth, tenants, users, invitations, roles, permissions, groups
from modulos.rrhh.endpoints import router as rrhh_router
from modulos.nomina.endpoints import router as nomina_router
from app.core.config import settings
from app.db.session import Base, engine

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    # Tables created by Alembic in production; here for dev convenience
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
    # Seed permisos módulo RRHH
    from app.db.session import SessionLocal
    from modulos.rrhh.permissions import seed_permissions
    from modulos.nomina.permissions import seed_permissions as seed_nomina

    with SessionLocal() as db:
        n = seed_permissions(db)
        if n:
            logger.info(f"RRHH: {n} permisos nuevos registrados")
        n = seed_nomina(db)
        if n:
            logger.info(f"Nómina: {n} permisos nuevos registrados")
    yield
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None,  # Manejado manualmente para servir JS localmente
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,  # required for cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
    expose_headers=["X-Total-Count"],
)

# ── Security Headers Middleware ───────────────────────────────────────────────

@app.middleware("http")
async def security_headers(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "worker-src blob:; "
        "connect-src 'self';"
    )
    response.headers["X-Response-Time"] = f"{(time.time() - start) * 1000:.1f}ms"
    return response


# ── Global exception handler (prevents stack trace leakage) ──────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."},
    )


# ── Routes ────────────────────────────────────────────────────────────────────

prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=prefix)
app.include_router(tenants.router, prefix=prefix)
app.include_router(users.router, prefix=prefix)
app.include_router(roles.router, prefix=prefix)
app.include_router(permissions.router, prefix=prefix)
app.include_router(groups.router, prefix=prefix)
app.include_router(rrhh_router, prefix=prefix)
app.include_router(nomina_router, prefix=prefix)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── ReDoc local (sin CDN externo) ─────────────────────────────────────────────

# ── ReDoc local (sin CDN externo) ─────────────────────────────────────────────

if settings.DEBUG:
    @app.get("/api/redoc", include_in_schema=False, response_class=HTMLResponse)
    async def redoc_html():
        return HTMLResponse("""
<!DOCTYPE html>
<html>
  <head>
    <title>ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
  </head>
  <body>
    <redoc spec-url='/api/openapi.json'></redoc>
    <script src="/static/bundles/redoc.standalone.js"></script>
  </body>
</html>
""")


# ── Static files ──────────────────────────────────────────────────────────────
# Estáticos internos (ReDoc JS, etc.) — debe ir ANTES del mount del frontend
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except RuntimeError:
    pass  # directorio no presente

# Frontend SPA — debe ir AL FINAL para no interceptar rutas de la API
try:
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
except RuntimeError:
    pass  # frontend dir not present