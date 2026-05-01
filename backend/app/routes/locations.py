"""
Ruta HTTP que expone el catálogo de estados y municipios soportados.

Es la fuente que el frontend consume para construir los selects en la UI.
"""

from typing import Dict

from fastapi import APIRouter

from app.core.locations import LOCATIONS, StateData

router = APIRouter(tags=["locations"])


@router.get(
    "/locations",
    summary="Catálogo de estados y municipios soportados",
    response_description=(
        "Mapa nombre_estado → {estado_id, municipios: {nombre_municipio: municipio_id}}"
    ),
)
def get_locations() -> Dict[str, StateData]:
    """
    Devuelve el catálogo completo para poblar los selects del cliente.

    Returns:
        Diccionario con estados como clave; cada valor incluye ``estado_id`` y
        un mapa ``municipios`` (nombre→id).
    """
    return LOCATIONS
