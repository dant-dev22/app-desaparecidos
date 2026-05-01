"""
Configuración centralizada de la aplicación.

Define URL base del REPD Jalisco, timeout HTTP y constantes para la API pública.
"""

import os

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

# Límites razonables para códigos CONABIO/INEGI de entidad federativa en México (1–32).
ESTADO_ID_MIN: int = 1
ESTADO_ID_MAX: int = 32
