"""
Rutas HTTP relacionadas con el cálculo de riesgo basado en datos REPD.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from requests import exceptions as req_exc

from app.core.config import MUNICIPIOS
from app.domain.filters import filter_persons
from app.domain.scoring import calculate_score
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
        ge=0.4,
        le=2.5,
        description="Estatura de referencia en metros (opcional; p. ej. 1.75)",
    ),
) -> RiskResponse:
    """
    Calcula score y nivel de riesgo según casos REPD filtrados y similitud con el perfil indicado.

    Args:
        municipio: Nombre del municipio (clave en el mapeo interno).
        edad: Edad para la ventana ±3 años.
        sexo: Debe coincidir exactamente con el valor en REPD (p. ej. HOMBRE).
        estatura: Metros; opcional. Si se omite, no se pondera la similitud de estatura.

    Returns:
        ``RiskResponse`` con score, nivel, casos_similares y municipio.

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

    filtered = filter_persons(raw, edad=edad, sexo=sexo)
    user_input: Dict[str, Any] = {"edad": edad, "sexo": sexo}
    if estatura is not None:
        user_input["estatura"] = estatura
    metrics = calculate_score(filtered, user_input)

    return RiskResponse(
        score=metrics["score"],
        nivel=metrics["nivel"],
        casos_similares=metrics["casos_similares"],
        municipio=key,
    )
