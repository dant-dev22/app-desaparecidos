"""
Esquemas Pydantic para respuestas de la API HTTP.
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field


class CasoSimilar(BaseModel):
    """Un caso REPD similar con identificador de cédula y ruta de foto."""

    id_cedula_busqueda: Optional[Union[int, str]] = Field(
        None,
        description="Identificador de cédula de búsqueda (REPD)",
    )
    ruta_foto: Optional[str] = Field(None, description="Ruta o URL de la fotografía")


class RiskResponse(BaseModel):
    """
    Respuesta del endpoint de evaluación de riesgo por similitud de casos REPD.

    Attributes:
        score: Puntuación numérica agregada (pesos por similitud y recencia).
        nivel: Nivel cualitativo: bajo, medio o alto.
        casos_similares: Lista de casos similares (id y ruta de foto por registro).
        total_casos_similares: Cantidad de casos similares (también suma 1 punto cada uno al score).
        municipio: Nombre del municipio solicitado (normalizado).
        colonia: Colonia usada para acotar el cálculo; null si se consideró todo el municipio.
    """

    score: float = Field(..., ge=0, description="Puntuación por pesos de similitud, recencia y volumen")
    nivel: str = Field(..., description="Nivel de riesgo: bajo, medio o alto")
    casos_similares: List[CasoSimilar] = Field(
        default_factory=list,
        description="Casos similares con id_cedula_busqueda y ruta_foto",
    )
    total_casos_similares: int = Field(
        ...,
        ge=0,
        description="Número de casos similares (un punto por caso incluido en el score)",
    )
    municipio: str = Field(..., description="Municipio consultado")
    colonia: Optional[str] = Field(
        None,
        description="Colonia del filtro (normalizada); omitida o null si el ámbito fue el municipio completo",
    )
