"""
Aplicación FastAPI: backend que consume REPD Jalisco y expone evaluación de riesgo.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.routes.locations import router as locations_router
from app.routes.risk import router as risk_router

setup_logging()

API_PREFIX = "/api"

app = FastAPI(
    title="REPD Risk API",
    description=(
        "API que consulta la versión pública de cédulas de búsqueda del REPD Jalisco, "
        "filtra por edad y sexo en servidor y devuelve un score de casos similares."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(locations_router, prefix=API_PREFIX)
app.include_router(risk_router, prefix=API_PREFIX)
