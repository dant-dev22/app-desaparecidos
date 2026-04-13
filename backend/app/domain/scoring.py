"""
Cálculo de puntuación de riesgo a partir de casos filtrados similares.

Combina similitud con el perfil del usuario y atributos de cada caso (recencia,
estatus, condición de localización) en un score agregado.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional


def normalize_string(value: Any) -> Optional[str]:
    """
    Normaliza texto para comparaciones: elimina espacios, mayúsculas y descarta vacíos.

    Args:
        value: Cadena u otro valor; ``None`` y cadenas vacías tras trim se tratan como ausentes.

    Returns:
        Cadena en mayúsculas sin bordes, o ``None`` si no hay texto utilizable.
    """
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
    else:
        s = str(value).strip()
    if not s:
        return None
    return s.upper()


def _parse_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        t = value.strip()
        if not t:
            return None
        try:
            return float(t.replace(",", "."))
        except ValueError:
            return None
    return None


def _parse_optional_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        t = value.strip()
        if not t:
            return None
        try:
            return int(t)
        except ValueError:
            return None
    return None


def _parse_fecha_desaparicion(value: Any) -> Optional[date]:
    """Interpreta ``fecha_desaparicion`` como fecha local (string u objetos date/datetime)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if "T" in s:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except ValueError:
            s = s.split("T", 1)[0]
    if len(s) >= 10:
        head = s[:10]
        try:
            return date.fromisoformat(head)
        except ValueError:
            pass
        for fmt in ("%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(head, fmt).date()
            except ValueError:
                continue
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _recency_points(fecha_desaparicion: Optional[date]) -> float:
    if fecha_desaparicion is None:
        return 0.0
    today = date.today()
    dias = (today - fecha_desaparicion).days
    if dias < 0:
        dias = 0
    return max(0.0, 5.0 - (dias / 30.0))


def _points_estatus_persona(estatus_norm: Optional[str]) -> int:
    if estatus_norm is None:
        return 0
    if estatus_norm == "PERSONA DESAPARECIDA":
        return 3
    if estatus_norm == "PERSONA LOCALIZADA":
        return 0
    return 0


def _points_condicion_localizacion(cond_norm: Optional[str]) -> int:
    if cond_norm is None:
        return 0
    if cond_norm == "SIN VIDA":
        return 5
    if cond_norm == "CON VIDA":
        return 1
    if cond_norm == "NO APLICA":
        return 2
    return 0


def _subscore_person(person: Dict[str, Any], user_input: Dict[str, Any]) -> float:
    total = 0.0

    user_edad = user_input.get("edad")
    if isinstance(user_edad, int):
        edad_reg = _parse_optional_int(person.get("edad_momento_desaparicion"))
        if edad_reg is not None and abs(edad_reg - user_edad) <= 3:
            total += 2.0

    user_sexo = normalize_string(user_input.get("sexo"))
    sexo_reg = normalize_string(person.get("sexo"))
    if user_sexo is not None and sexo_reg is not None and user_sexo == sexo_reg:
        total += 2.0

    user_estatura = _parse_optional_float(user_input.get("estatura"))
    if user_estatura is not None:
        reg_estatura = _parse_optional_float(person.get("estatura"))
        if reg_estatura is not None and abs(reg_estatura - user_estatura) < 0.10:
            total += 1.0

    fecha = _parse_fecha_desaparicion(person.get("fecha_desaparicion"))
    total += _recency_points(fecha)

    estatus_norm = normalize_string(person.get("estatus_persona_desaparecida"))
    total += float(_points_estatus_persona(estatus_norm))

    cond_norm = normalize_string(person.get("condicion_localizacion"))
    total += float(_points_condicion_localizacion(cond_norm))

    return total


def calculate_score(
    filtered_list: List[Dict[str, Any]],
    user_input: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calcula el score y nivel de riesgo sumando sub-puntuaciones por cada caso filtrado.

    Cada registro aporta puntos por proximidad de edad, sexo, estatura (si aplica),
    recencia de la desaparición, estatus de la persona y condición de localización.

    Args:
        filtered_list: Registros que pasaron ``filter_persons``.
        user_input: Perfil de referencia con al menos ``edad`` (int) y ``sexo`` (str);
            ``estatura`` (float, metros) es opcional.

    Returns:
        Diccionario con ``score`` (suma de sub-puntuaciones), ``nivel`` (bajo/medio/alto)
        según umbrales actuales, y ``casos_similares`` (cantidad de registros en la lista).
    """
    total_score = sum(_subscore_person(p, user_input) for p in filtered_list)
    casos_similares = len(filtered_list)

    if total_score <= 20:
        nivel = "bajo"
    elif total_score <= 50:
        nivel = "medio"
    else:
        nivel = "alto"

    return {
        "score": round(total_score, 2),
        "nivel": nivel,
        "casos_similares": casos_similares,
    }
