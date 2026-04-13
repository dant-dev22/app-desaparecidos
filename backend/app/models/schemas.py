"""
Esquemas Pydantic para respuestas de la API HTTP.
"""

from pydantic import BaseModel, Field


class RiskResponse(BaseModel):
    """
    Respuesta del endpoint de evaluación de riesgo por similitud de casos REPD.

    Attributes:
        score: Puntuación numérica agregada (pesos por similitud y por caso).
        nivel: Nivel cualitativo: bajo, medio o alto.
        casos_similares: Cantidad de registros que coinciden con los criterios.
        municipio: Nombre del municipio solicitado (normalizado).
    """

    score: float = Field(..., ge=0, description="Puntuación agregada por similitud y atributos de casos")
    nivel: str = Field(..., description="Nivel de riesgo: bajo, medio o alto")
    casos_similares: int = Field(..., ge=0, description="Número de casos similares")
    municipio: str = Field(..., description="Municipio consultado")
