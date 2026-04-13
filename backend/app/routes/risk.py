"""
Rutas HTTP relacionadas con el cálculo de riesgo basado en datos REPD.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from requests import exceptions as req_exc

from app.core.config import MUNICIPIOS
from app.domain.filters import filter_persons
from app.domain.scoring import calculate_score, normalize_string
from app.models.schemas import RiskResponse
from app.services.repd_client import RepdClient

router = APIRouter(tags=["risk"])

_repd_client = RepdClient()


@router.get(
    "/risk",
    response_model=RiskResponse,
    summary="Riesgo por similitud de casos desaparecidos (REPD Jalisco)",
)
def get_risk(
    municipio: str = Query(
        ...,
        description="Municipio: guadalajara, zapopan, tonala, tlaquepaque, tlajomulco",
        examples=["guadalajara"],
    ),
    edad: int = Query(..., ge=0, le=120, description="Edad de referencia (±3 años en filtro)"),
    sexo: str = Query(
        ...,
        description="Sexo exacto según REPD: HOMBRE o MUJER",
        examples=["HOMBRE"],
    ),
    estatura: Optional[float] = Query(
        None,
        ge=0.5,
        le=2.5,
        description="Estatura en metros (opcional); si se omite no aplica bonus por estatura",
    ),
    colonia: Optional[str] = Query(
        None,
        description=(
            "Opcional. Si se envía, solo se consideran registros REPD cuyo campo colonia "
            "coincide (trim y mayúsculas). Si se omite, el cálculo usa todo el municipio."
        ),
        examples=["CENTRO HISTÓRICO"],
    ),
) -> RiskResponse:
    """
    Calcula score y nivel de riesgo según casos REPD: municipio (consulta REPD), opcionalmente
    acotado por colonia, más edad y sexo.

    Args:
        municipio: Nombre del municipio (clave en el mapeo interno).
        edad: Edad para la ventana ±3 años.
        sexo: Debe coincidir exactamente con el valor en REPD (p. ej. HOMBRE).
        estatura: Opcional; si se envía, puede sumar peso si coincide con el registro.
        colonia: Opcional; filtra por el campo ``colonia`` de la API; sin ella, ámbito municipal.

    Returns:
        ``RiskResponse`` con score, nivel, casos, total_casos_similares, municipio y colonia.

    Raises:
        HTTPException: 400 si el municipio no está soportado; 502/504 según fallo REPD.
    """
    key = municipio.strip().lower()
    if key not in MUNICIPIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Municipio no válido: {municipio}. Válidos: {', '.join(sorted(MUNICIPIOS.keys()))}",
        )

    municipio_id = MUNICIPIOS[key]

    try:
        raw = _repd_client.fetch_cedulas(municipio_id)
    except req_exc.Timeout as e:
        raise HTTPException(status_code=504, detail="Tiempo de espera agotado al consultar REPD") from e
    except req_exc.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail="El servicio REPD respondió con error",
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except req_exc.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al consultar REPD: {type(e).__name__}",
        ) from e

    filtered = filter_persons(raw, edad=edad, sexo=sexo, colonia=colonia)
    user_input = {"edad": edad, "sexo": sexo, "estatura": estatura}
    metrics = calculate_score(filtered, user_input)

    colonia_resp: Optional[str] = normalize_string(colonia) if colonia else None

    return RiskResponse(
        score=metrics["score"],
        nivel=metrics["nivel"],
        casos_similares=metrics["casos_similares"],
        total_casos_similares=metrics["total_casos_similares"],
        municipio=key,
        colonia=colonia_resp,
    )
