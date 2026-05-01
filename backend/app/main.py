"""
Aplicación FastAPI: backend que consume REPD Jalisco y expone evaluación de riesgo.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import (
    cors_allow_origins,
    openapi_docs_enabled,
    trusted_allowed_hosts,
)
from app.core.logging import setup_logging
from app.routes.locations import router as locations_router
from app.routes.risk import router as risk_router

setup_logging()

API_PREFIX = "/api"


def _openapi_kwargs():
    if openapi_docs_enabled():
        return {}
    return {
        "openapi_url": None,
        "docs_url": None,
        "redoc_url": None,
    }


app = FastAPI(
    title="REPD Risk API",
    description=(
        "API que consulta la versión pública de cédulas de búsqueda del REPD Jalisco, "
        "filtra por edad y sexo en servidor y devuelve un score de casos similares."
    ),
    version="1.0.0",
    **_openapi_kwargs(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins(),
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

hosts = trusted_allowed_hosts()
if hosts:
    # Último en registrarse corre primero: valida Host antes del resto.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response


app.include_router(locations_router, prefix=API_PREFIX)
app.include_router(risk_router, prefix=API_PREFIX)
