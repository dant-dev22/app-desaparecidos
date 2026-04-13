"""
Cliente HTTP para la API pública REPD (cédulas de búsqueda), Jalisco.

Responsable de construir URLs y obtener respuestas JSON, con manejo de errores
de red y HTTP, y registro en log.
"""

from typing import Any, Dict, List

import requests
from requests import exceptions as req_exc

from app.core.config import BASE_URL, CEDULAS_PAGE_LIMIT, ESTADO_JALISCO, TIMEOUT
from app.core.logging import get_logger

logger = get_logger("repd_client")

CEDULAS_PATH: str = "repd-version-publica-cedulas-busqueda/"


class RepdClient:
    """
    Cliente para consultar cédulas de búsqueda por municipio.

    Attributes:
        timeout: Segundos máximos de espera por petición HTTP.
    """

    def __init__(self, timeout: int = TIMEOUT) -> None:
        """
        Inicializa el cliente con timeout configurable.

        Args:
            timeout: Timeout en segundos para ``requests``.
        """
        self.timeout = timeout

    def build_url(self, municipio_id: int) -> str:
        """
        Construye la URL absoluta del endpoint con estado y municipio.

        Args:
            municipio_id: Identificador numérico del municipio en la API.

        Returns:
            URL completa lista para GET (parámetros de página se añaden en fetch).
        """
        base = BASE_URL.rstrip("/") + "/"
        path = CEDULAS_PATH.lstrip("/")
        return f"{base}{path}?estado={ESTADO_JALISCO}&municipio={municipio_id}"

    def fetch_cedulas(self, municipio_id: int) -> Dict[str, Any]:
        """
        Obtiene todas las cédulas disponibles para el municipio (paginación interna).

        Args:
            municipio_id: Identificador del municipio.

        Returns:
            Diccionario con ``count``, ``total_pages`` y ``results`` (lista fusionada).

        Raises:
            req_exc.Timeout: Si la petición excede el timeout.
            req_exc.HTTPError: Si el código de estado no es 200.
            ValueError: Si la respuesta no es JSON válido.
        """
        all_results: List[Dict[str, Any]] = []
        page = 1
        limit = CEDULAS_PAGE_LIMIT
        total_pages: int = 1

        while page <= total_pages:
            url = self.build_url(municipio_id)
            url = f"{url}&page={page}&limit={limit}"
            logger.info("Solicitando cédulas REPD: municipio_id=%s page=%s", municipio_id, page)

            try:
                response = requests.get(url, timeout=self.timeout)
            except req_exc.Timeout as e:
                logger.error("Timeout al contactar REPD: %s", e)
                raise
            except req_exc.RequestException as e:
                logger.error("Error de red al contactar REPD: %s", e)
                raise

            if response.status_code != 200:
                logger.error(
                    "REPD respondió status=%s body=%s",
                    response.status_code,
                    response.text[:500],
                )
                response.raise_for_status()

            try:
                payload: Dict[str, Any] = response.json()
            except ValueError as e:
                logger.error("Respuesta no JSON del REPD: %s", e)
                raise ValueError("La API REPD no devolvió JSON válido") from e

            total_pages = max(1, int(payload.get("total_pages", 1)))
            batch = payload.get("results") or []
            if not isinstance(batch, list):
                batch = []
            all_results.extend(batch)
            page += 1

        return {
            "count": len(all_results),
            "total_pages": total_pages,
            "results": all_results,
        }
