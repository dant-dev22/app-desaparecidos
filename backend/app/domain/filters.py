"""
Filtros de negocio sobre registros de personas desaparecidas (REPD).

Aplica reglas de edad, sexo y estatus que la API externa no garantiza por sí sola.
"""

from typing import Any, Dict, List


def filter_persons(data: Dict[str, Any], edad: int, sexo: str) -> List[Dict[str, Any]]:
    """
    Filtra la lista ``results`` del payload REPD según criterios del usuario.

    Ignora registros sin edad; exige coincidencia exacta de sexo; edad en ventana
    de ±3 años respecto a ``edad``; excluye personas ya localizadas.

    Args:
        data: Diccionario con clave ``results`` (lista de dicts) como devuelve REPD.
        edad: Edad de referencia para la ventana ±3 años.
        sexo: Valor exacto esperado (p. ej. ``HOMBRE`` o ``MUJER``).

    Returns:
        Lista de diccionarios de persona que cumplen todos los criterios.
    """
    results = data.get("results")
    if not isinstance(results, list):
        return []

    sexo_norm = sexo.strip().upper()
    filtered: List[Dict[str, Any]] = []

    for item in results:
        if not isinstance(item, dict):
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

        filtered.append(item)

    return filtered
