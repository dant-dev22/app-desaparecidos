"""
Configuración de logging para la aplicación.

Propósito: unificar formato y nivel de logs en consola para el cliente REPD y rutas.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configura el logging raíz con formato estándar y salida a stderr.

    Args:
        level: Nivel de logging (por defecto INFO).
    """
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Devuelve un logger con nombre jerárquico bajo `app`.

    Args:
        name: Sufijo del nombre del logger (ej. ``repd_client``).

    Returns:
        Instancia configurada de ``logging.Logger``.
    """
    setup_logging()
    full_name = f"app.{name}" if name else "app"
    return logging.getLogger(full_name)
