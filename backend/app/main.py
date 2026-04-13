"""
Aplicación FastAPI: backend que consume REPD Jalisco y expone evaluación de riesgo.
"""

from fastapi import FastAPI

from app.core.logging import setup_logging
from app.routes.risk import router as risk_router

setup_logging()

app = FastAPI(
    title="REPD Risk API",
    description=(
        "API que consulta la versión pública de cédulas de búsqueda del REPD Jalisco, "
        "filtra por edad y sexo en servidor y devuelve un score de casos similares."
    ),
    version="1.0.0",
)

app.include_router(risk_router)
