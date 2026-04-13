"""
Filtros de negocio sobre registros de personas desaparecidas (REPD).

Aplica reglas de edad, sexo y estatus que la API externa no garantiza por sí sola.
"""

from typing import Any, Dict, List, Optional

from app.domain.scoring import normalize_string


def _autorizacion_publica_si(value: Any) -> bool:
    """True si el valor, tras trim y mayúsculas, es ``SI``."""
    if value is None or not isinstance(value, str):
        return False
    return value.strip().upper() == "SI"


def filter_persons(
    data: Dict[str, Any],
    edad: int,
    sexo: str,
    colonia: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filtra la lista ``results`` del payload REPD según criterios del usuario.

    Solo incluye registros con ``autorizacion_informacion_publica`` normalizado a ``SI``.
    Ignora registros sin edad; exige coincidencia exacta de sexo; edad en ventana
    de ±3 años respecto a ``edad``; excluye personas ya localizadas.
    Si ``colonia`` tiene texto, solo incluye filas cuyo campo ``colonia`` (API) coincide
    tras normalizar (trim y mayúsculas). Si ``colonia`` es ``None`` o vacío, no se filtra
    por colonia (ámbito de todo el municipio obtenido por la consulta).

    Args:
        data: Diccionario con clave ``results`` (lista de dicts) como devuelve REPD.
        edad: Edad de referencia para la ventana ±3 años.
        sexo: Valor exacto esperado (p. ej. ``HOMBRE`` o ``MUJER``).
        colonia: Opcional; si se indica, debe coincidir con ``item["colonia"]`` del REPD.

    Returns:
        Lista de diccionarios de persona que cumplen todos los criterios.
    """
    results = data.get("results")
    if not isinstance(results, list):
        return []

    sexo_norm = sexo.strip().upper()
    colonia_norm = normalize_string(colonia) if colonia else None
    filtered: List[Dict[str, Any]] = []

    for item in results:
        if not isinstance(item, dict):
            continue

        if not _autorizacion_publica_si(item.get("autorizacion_informacion_publica")):
            continue

        edad_reg = item.get("edad_momento_desaparicion")
        if edad_reg is None:
            continue
        try:
            edad_int = int(edad_reg)
        except (TypeError, ValueError):
            continue

        if abs(edad_int - edad) > 3:
            continue

        sexo_reg = item.get("sexo")
        if not isinstance(sexo_reg, str) or sexo_reg.strip().upper() != sexo_norm:
            continue

        estatus = item.get("estatus_persona_desaparecida")
        if isinstance(estatus, str) and estatus.strip().upper() == "PERSONA LOCALIZADA":
            continue

        if colonia_norm is not None:
            reg_col = normalize_string(item.get("colonia"))
            if reg_col != colonia_norm:
                continue

        filtered.append(item)

    return filtered
