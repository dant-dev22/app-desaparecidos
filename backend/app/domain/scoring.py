"""
Cálculo de puntuación de riesgo a partir de casos filtrados similares.

Agrega pesos por similitud (edad, sexo, estatura), recencia, estatus y condición.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional


def normalize_string(value: Any) -> Optional[str]:
    """
    Normaliza texto para comparaciones: acepta null, recorta y pasa a mayúsculas.

    Args:
        value: Valor crudo (típicamente str); otro tipo o vacío → None.

    Returns:
        Cadena normalizada o None si no hay texto útil.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    return s.upper()


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace(",", ".")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return int(float(s.replace(",", ".")))
        except ValueError:
            return None
    return None


def _texto_opcional_rep(value: Any) -> Optional[str]:
    """Cadena ``str`` del REPD tras trim; vacía u otro tipo → None."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s if s else None


def _fecha_desaparicion_respuesta(person: Dict[str, Any]) -> Optional[str]:
    """Valor serializable para la API: ISO si hay fecha parseable, si no el string crudo."""
    raw = person.get("fecha_desaparicion")
    parsed = parse_fecha_desaparicion(raw)
    if parsed is not None:
        return parsed.isoformat()
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def parse_fecha_desaparicion(value: Any) -> Optional[date]:
    """
    Interpreta fecha_desaparicion desde tipos habituales (date, datetime, ISO string).

    Args:
        value: Valor del registro REPD.

    Returns:
        Fecha local del hecho o None si no es posible interpretarla.
    """
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
        s = s.split("T", 1)[0]
    s_iso = s.replace("Z", "+00:00")
    for candidate in (s, s_iso):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt.date()
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _recency_points(fecha_desaparicion: Optional[date], today: date) -> float:
    if fecha_desaparicion is None:
        return 0.0
    dias = (today - fecha_desaparicion).days
    if dias < 0:
        return 0.0
    return max(0.0, 5.0 - (dias / 30.0))


def _estatus_distinto_de_persona_localizada(estatus_raw: Any) -> bool:
    return normalize_string(estatus_raw) != "PERSONA LOCALIZADA"


def _estatus_points(estatus_raw: Any) -> float:
    n = normalize_string(estatus_raw)
    if n is None:
        return 0.0
    if n == "PERSONA DESAPARECIDA":
        return 3.0
    if n == "PERSONA LOCALIZADA":
        return 0.0
    return 0.0


def _condicion_points(condicion_raw: Any) -> float:
    n = normalize_string(condicion_raw)
    if n is None:
        return 0.0
    if n == "SIN VIDA":
        return 5.0
    if n == "CON VIDA":
        return 1.0
    if n == "NO APLICA":
        return 2.0
    return 0.0


def _edad_points(person: Dict[str, Any], user_edad: int) -> float:
    edad_reg = _to_int(person.get("edad_momento_desaparicion"))
    if edad_reg is None:
        return 0.0
    if abs(edad_reg - user_edad) <= 3:
        return 2.0
    return 0.0


def _sexo_points(person: Dict[str, Any], user_sexo_norm: str) -> float:
    n = normalize_string(person.get("sexo"))
    if n is None:
        return 0.0
    if n == user_sexo_norm:
        return 2.0
    return 0.0


def _estatura_points(person: Dict[str, Any], user_estatura: Optional[float]) -> float:
    if user_estatura is None:
        return 0.0
    est_reg = _to_float(person.get("estatura"))
    if est_reg is None:
        return 0.0
    if abs(est_reg - user_estatura) < 0.10:
        return 1.0
    return 0.0


def extract_image_url(person: Dict[str, Any]) -> Optional[str]:
    """
    Obtiene la ruta o URL de la imagen desde ``ruta_foto`` (REPD).

    Args:
        person: Diccionario de persona (REPD).

    Returns:
        Cadena no vacía o None.
    """
    v = person.get("ruta_foto")
    if isinstance(v, str):
        u = v.strip()
        if u:
            return u
    return None


def _prioritize_persons_para_casos_similares(
    personas: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Ordena registros para la respuesta: prioriza estatus distinto de PERSONA LOCALIZADA y,
    dentro de ese criterio, quienes traen ``ruta_foto`` no vacía. Con 3 o más casos totales,
    los tres primeros de la lista agrupan antes a quienes suelen tener ``ruta_foto`` poblada en
    REPD cuando existen suficientes registros así.
    """
    validas = [p for p in personas if isinstance(p, dict)]

    decorated: List[tuple[tuple, Dict[str, Any]]] = []
    for p in validas:
        dl = _estatus_distinto_de_persona_localizada(p.get("estatus_persona_desaparecida"))
        foto = extract_image_url(p)
        orden = (
            not dl,
            foto is None,
            str(p.get("id_cedula_busqueda") or ""),
        )
        decorated.append((orden, p))

    decorated.sort(key=lambda t: t[0])
    return [p for _, p in decorated]


def _sub_score_for_person(
    person: Dict[str, Any],
    user_edad: int,
    user_sexo_norm: str,
    user_estatura: Optional[float],
    today: date,
) -> float:
    total = 0.0
    total += _edad_points(person, user_edad)
    total += _sexo_points(person, user_sexo_norm)
    total += _estatura_points(person, user_estatura)
    total += _recency_points(parse_fecha_desaparicion(person.get("fecha_desaparicion")), today)
    total += _estatus_points(person.get("estatus_persona_desaparecida"))
    total += _condicion_points(person.get("condicion_localizacion"))
    return total


def calculate_score(
    filtered_list: List[Dict[str, Any]],
    user_input: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calcula score agregado y nivel de riesgo a partir de casos filtrados y datos del usuario.

    El score es la suma de sub-scores por persona (similitud de edad ±3 años, sexo, estatura,
    recencia, estatus y condición) **más un punto por cada caso similar** (volumen).
    Si en esos registros hay al menos dos con estatus distinto de PERSONA LOCALIZADA, el peso del
    término de volumen se duplica (**mayor intensidad**).
    ``total_casos_similares`` es ``len(casos_similares)`` y entra en ese aporte al score final.
    ``casos_similares`` incluye todos los registros ordenados para la respuesta: primero los de
    estatus distinto de PERSONA LOCALIZADA y, entre ellos, quienes traen ``ruta_foto`` así, con
    tres o más casos globales los primeros de la lista suelen tener foto cuando REPD las suministra.

    Args:
        filtered_list: Registros que pasaron ``filter_persons``.
        user_input: Debe incluir ``edad`` (int) y ``sexo`` (str); ``estatura`` (float) es opcional.

    Returns:
        Diccionario con ``score``, ``nivel``, ``casos_similares``, ``total_casos_similares``.
    """
    edad = _to_int(user_input.get("edad"))
    if edad is None:
        edad = 0
    user_sexo_norm = normalize_string(user_input.get("sexo")) or ""
    user_estatura = _to_float(user_input.get("estatura"))

    today = date.today()
    total_score = 0.0
    casos_distintos_localizada = 0

    personas_validas = [p for p in filtered_list if isinstance(p, dict)]

    for person in personas_validas:
        if _estatus_distinto_de_persona_localizada(person.get("estatus_persona_desaparecida")):
            casos_distintos_localizada += 1
        total_score += _sub_score_for_person(
            person,
            user_edad=edad,
            user_sexo_norm=user_sexo_norm,
            user_estatura=user_estatura,
            today=today,
        )

    personas_ord = _prioritize_persons_para_casos_similares(personas_validas)
    casos_similares: List[Dict[str, Any]] = []
    for person in personas_ord:
        nombre = person.get("nombre_completo")
        nombre_str = nombre.strip() if isinstance(nombre, str) else None
        if nombre_str == "":
            nombre_str = None
        casos_similares.append(
            {
                "id_cedula_busqueda": person.get("id_cedula_busqueda"),
                "ruta_foto": extract_image_url(person),
                "nombre_completo": nombre_str,
                "edad_momento_desaparicion": _to_int(person.get("edad_momento_desaparicion")),
                "estatura": _to_float(person.get("estatura")),
                "tez": _texto_opcional_rep(person.get("tez")),
                "ojos_color": _texto_opcional_rep(person.get("ojos_color")),
                "fecha_desaparicion": _fecha_desaparicion_respuesta(person),
            }
        )

    total_casos_similares = len(casos_similares)
    volume = float(total_casos_similares)
    if casos_distintos_localizada >= 2:
        total_score += volume * 2.0
    else:
        total_score += volume

    if total_score <= 20:
        nivel = "bajo"
    elif total_score <= 50:
        nivel = "medio"
    else:
        nivel = "alto"

    return {
        "score": round(total_score, 4),
        "nivel": nivel,
        "casos_similares": casos_similares,
        "total_casos_similares": total_casos_similares,
    }
