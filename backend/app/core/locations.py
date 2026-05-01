"""
Catálogo de estados y municipios soportados con sus códigos numéricos.

El catálogo es la fuente única de verdad que el frontend consume para construir
los selects de estado y municipio. Los códigos numéricos coinciden con los que
la API REPD espera en sus parámetros ``estado`` y ``municipio``.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, Optional, Tuple, TypedDict


class StateData(TypedDict):
    """Bloque de un estado en el catálogo: su id y el mapa nombre→id de municipios."""

    estado_id: int
    municipios: Dict[str, int]


# Catálogo. Las claves de estado y municipio están en MAYÚSCULAS sin diacríticos en su
# mayoría; las variantes con ñ se conservan tal cual aparecen en los registros REPD.
LOCATIONS: Dict[str, StateData] = {
    "GUANAJUATO": {
        "estado_id": 11,
        "municipios": {
            "LEON": 11020,
        },
    },
    "JALISCO": {
        "estado_id": 14,
        "municipios": {
            "ACATIC": 14001,
            "ACATLAN DE JUAREZ": 14002,
            "AHUALULCO DE MERCADO": 14003,
            "AMATITAN": 14005,
            "AMECA": 14006,
            "ARANDAS": 14008,
            "ATEMAJAC DE BRIZUELA": 14010,
            "ATENGUILLO": 14012,
            "ATOTONILCO EL ALTO": 14013,
            "ATOYAC": 14014,
            "AUTLAN DE NAVARRO": 14015,
            "AYOTLAN": 14016,
            "AYUTLA": 14017,
            "BOLAÑOS": 14019,
            "CABO CORRIENTES": 14020,
            "CAÑADAS DE OBREGON": 14117,
            "CASIMIRO CASTILLO": 14021,
            "CHAPALA": 14030,
            "CIHUATLAN": 14022,
            "COCULA": 14024,
            "COLOTLAN": 14025,
            "CONCEPCION DE BUENOS AIRES": 14026,
            "CUAUTITLAN DE GARCIA BARRAGAN": 14027,
            "CUAUTLA": 14028,
            "CUQUIO": 14029,
            "DEGOLLADO": 14033,
            "EL ARENAL": 14009,
            "EL GRULLO": 14037,
            "EL LIMON": 14054,
            "EL SALTO": 14070,
            "ENCARNACION DE DIAZ": 14035,
            "ETZATLAN": 14036,
            "GOMEZ FARIAS": 14079,
            "GUACHINANGO": 14038,
            "GUADALAJARA": 14039,
            "HOSTOTIPAQUILLO": 14040,
            "HUEJUCAR": 14041,
            "HUEJUQUILLA EL ALTO": 14042,
            "IXTLAHUACAN DE LOS MEMBRILLOS": 14044,
            "IXTLAHUACAN DEL RIO": 14045,
            "JALOSTOTITLAN": 14046,
            "JAMAY": 14047,
            "JESUS MARIA": 14048,
            "JILOTLAN DE LOS DOLORES": 14049,
            "JOCOTEPEC": 14050,
            "JUANACATLAN": 14051,
            "JUCHITLAN": 14052,
            "LA BARCA": 14018,
            "LAGOS DE MORENO": 14053,
            "LA HUERTA": 14043,
            "LA MANZANILLA DE LA PAZ": 14057,
            "MAGDALENA": 14055,
            "MASCOTA": 14058,
            "MAZAMITLA": 14059,
            "MEZQUITIC": 14061,
            "MIXTLAN": 14062,
            "OCOTLAN": 14063,
            "OJUELOS DE JALISCO": 14064,
            "PIHUAMO": 14065,
            "PONCITLAN": 14066,
            "PUERTO VALLARTA": 14067,
            "QUITUPAN": 14069,
            "SAN CRISTOBAL DE LA BARRANCA": 14071,
            "SAN DIEGO DE ALEJANDRIA": 14072,
            "SAN GABRIEL": 14113,
            "SAN IGNACIO CERRO GORDO": 14125,
            "SAN JUAN DE LOS LAGOS": 14073,
            "SAN JUANITO DE ESCOBEDO": 14007,
            "SAN JULIAN": 14074,
            "SAN MARCOS": 14075,
            "SAN MARTIN HIDALGO": 14077,
            "SAN MIGUEL EL ALTO": 14078,
            "SAN PEDRO TLAQUEPAQUE": 14098,
            "SAN SEBASTIAN DEL OESTE": 14080,
            "SANTA MARIA DEL ORO": 14056,
            "SANTA MARIA DE LOS ANGELES": 14081,
            "SAYULA": 14082,
            "SE IGNORA": 14000,
            "TALA": 14083,
            "TALPA DE ALLENDE": 14084,
            "TAMAZULA DE GORDIANO": 14085,
            "TAPALPA": 14086,
            "TECALITLAN": 14087,
            "TECHALUTA DE MONTENEGRO": 14089,
            "TECOLOTLAN": 14088,
            "TENAMAXTLAN": 14090,
            "TEOCALTICHE": 14091,
            "TEOCUITATLAN DE CORONA": 14092,
            "TEPATITLAN DE MORELOS": 14093,
            "TEQUILA": 14094,
            "TEUCHITLAN": 14095,
            "TIZAPAN EL ALTO": 14096,
            "TLAJOMULCO DE ZUÑIGA": 14097,
            "TOLIMAN": 14099,
            "TOMATLAN": 14100,
            "TONALA": 14101,
            "TONAYA": 14102,
            "TONILA": 14103,
            "TOTATICHE": 14104,
            "TOTOTLAN": 14105,
            "TUXCACUESCO": 14106,
            "TUXCUECA": 14107,
            "TUXPAN": 14108,
            "UNION DE SAN ANTONIO": 14109,
            "UNION DE TULA": 14110,
            "VALLE DE GUADALUPE": 14111,
            "VALLE DE JUAREZ": 14112,
            "VILLA CORONA": 14114,
            "VILLA GUERRERO": 14115,
            "VILLA HIDALGO": 14116,
            "VILLA PURIFICACION": 14068,
            "YAHUALICA DE GONZALEZ GALLO": 14118,
            "ZACOALCO DE TORRES": 14119,
            "ZAPOPAN": 14120,
            "ZAPOTILTIC": 14121,
            "ZAPOTITLAN DE VADILLO": 14122,
            "ZAPOTLAN DEL REY": 14123,
            "ZAPOTLANEJO": 14124,
            "ZAPOTLAN EL GRANDE": 14023,
        },
    },
    "MEXICO": {
        "estado_id": 15,
        "municipios": {
            "NAUCALPAN DE JUAREZ": 15057,
        },
    },
    "MICHOACAN DE OCAMPO": {
        "estado_id": 16,
        "municipios": {
            "ACUITZIO": 16001,
            "MORELIA": 16053,
            "TARIMBARO": 16088,
        },
    },
}


def normalize_key(value: str) -> str:
    """
    Normaliza una etiqueta para comparaciones contra el catálogo.

    Quita diacríticos, pasa a mayúsculas, hace ``trim`` y colapsa espacios.

    Args:
        value: Texto crudo (nombre de estado o municipio).

    Returns:
        Texto normalizado; cadena vacía si la entrada no es texto útil.
    """
    if not isinstance(value, str):
        return ""
    nfd = unicodedata.normalize("NFD", value)
    no_marks = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return " ".join(no_marks.upper().split())


# Índices precomputados para búsquedas O(1) por nombre normalizado.
_STATE_INDEX: Dict[str, str] = {normalize_key(name): name for name in LOCATIONS}
_MUNI_INDEX: Dict[str, Dict[str, str]] = {
    name: {normalize_key(m): m for m in data["municipios"]}
    for name, data in LOCATIONS.items()
}


def find_state(value: str) -> Optional[str]:
    """Devuelve el nombre canónico del estado para un valor crudo o None."""
    return _STATE_INDEX.get(normalize_key(value))


def find_municipio(state_canonical: str, value: str) -> Optional[str]:
    """Devuelve el nombre canónico del municipio dentro de un estado canónico, o None."""
    municipios = _MUNI_INDEX.get(state_canonical)
    if not municipios:
        return None
    return municipios.get(normalize_key(value))


def resolve_ids(estado: str, municipio: str) -> Optional[Tuple[int, int, str, str]]:
    """
    Resuelve un par (estado, municipio) a sus IDs y nombres canónicos.

    Args:
        estado: Nombre del estado (cualquier casing/diacríticos).
        municipio: Nombre del municipio dentro del estado.

    Returns:
        Tupla ``(estado_id, municipio_id, estado_canonical, municipio_canonical)``
        o ``None`` si no existe en el catálogo.
    """
    state_canonical = find_state(estado)
    if state_canonical is None:
        return None
    muni_canonical = find_municipio(state_canonical, municipio)
    if muni_canonical is None:
        return None
    estado_id = LOCATIONS[state_canonical]["estado_id"]
    municipio_id = LOCATIONS[state_canonical]["municipios"][muni_canonical]
    return estado_id, municipio_id, state_canonical, muni_canonical
