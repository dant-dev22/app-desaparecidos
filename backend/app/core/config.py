"""
Configuración centralizada de la aplicación.

Define URL base del REPD Jalisco, timeout HTTP y mapeo de nombres de municipio
a identificadores numéricos usados por la API pública.
"""

import os
from typing import Dict

# URL base de la API pública de versiones de cédulas (REPD Jalisco).
BASE_URL: str = "https://repd.jalisco.gob.mx/api/v1/version_publica/"


def _read_timeout() -> int:
    """Lee REPD_HTTP_TIMEOUT del entorno; por defecto 30 s; mínimo 5 s."""
    raw = os.environ.get("REPD_HTTP_TIMEOUT", "30")
    try:
        return max(5, int(raw))
    except ValueError:
        return 30


# Timeout en segundos para cada petición HTTP al REPD (la API pública suele ser lenta).
TIMEOUT: int = _read_timeout()

# Registros por página al paginar el endpoint de cédulas (misma API, menos round-trips).
CEDULAS_PAGE_LIMIT: int = 100

# Código de estado (Jalisco) requerido por la API.
ESTADO_JALISCO: int = 14

# Mapeo nombre normalizado -> id de municipio en la API.
MUNICIPIOS: Dict[str, int] = {
    "guadalajara": 14039,
    "zapopan": 14070,
    "tonala": 14101,
    "tlaquepaque": 14098,
    "tlajomulco": 14097,
}
