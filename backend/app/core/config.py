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


def _env_truthy(name: str) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def openapi_docs_enabled() -> bool:
    """Si DISABLE_DOCS está activo, no se publican /docs, /redoc ni /openapi.json."""
    return not _env_truthy("DISABLE_DOCS")


def cors_allow_origins() -> list[str]:
    """Orígenes CORS: lista separada por comas en CORS_ALLOW_ORIGINS o ['*'] si no existe la variable."""
    raw = os.environ.get("CORS_ALLOW_ORIGINS")
    if raw is None:
        return ["*"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts if parts else ["*"]


def trusted_allowed_hosts() -> list[str] | None:
    """Hosts permitidos (cabecera Host). None = sin validación (adecuado en local detrás de 127.0.0.1)."""
    raw = os.environ.get("ALLOWED_HOSTS")
    if raw is None or not raw.strip():
        return None
    return [h.strip() for h in raw.split(",") if h.strip()]
