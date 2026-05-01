"""
Rutas HTTP relacionadas con el cálculo de riesgo basado en datos REPD.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from requests import exceptions as req_exc

from app.core.config import ESTADO_ID_MAX, ESTADO_ID_MIN
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
    estado: int = Query(
        ...,
        ge=ESTADO_ID_MIN,
        le=ESTADO_ID_MAX,
        description=(
            "Código numérico de la entidad federativa (ej. resultado de geo en el cliente; 1–32)."
        ),
        examples=[14],
    ),
    municipio_id: int = Query(
        ...,
        ge=1,
        le=99999,
        description=(
            "Identificador numérico del municipio esperado por la API REPD (enviado por el cliente, "
            "p. ej. CVEGEO)."
        ),
        examples=[14039],
    ),
    municipio_nombre: Optional[str] = Query(
        None,
        description="Nombre/localidad legible opcional desde geolocalización (se devuelve en la respuesta).",
        examples=["Guadalajara"],
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
    Calcula score y nivel de riesgo según casos REPD: estado y municipio (consulta REPD), opcionalmente
    acotado por colonia, más edad y sexo.

    Args:
        estado: Identificador de entidad federativa usado por la API REPD.
        municipio_id: Identificador del municipio usado por la API REPD (p. ej. desde geointel client).
        municipio_nombre: Opcional; nombre legible desde el cliente para la respuesta.
        edad: Edad para la ventana ±3 años.
        sexo: Debe coincidir exactamente con el valor en REPD (p. ej. HOMBRE).
        estatura: Opcional; si se envía, puede sumar peso si coincide con el registro.
        colonia: Opcional; filtra por el campo ``colonia`` de la API; sin ella, ámbito municipal.

    Returns:
        ``RiskResponse`` con score, nivel, casos, total_casos_similares, municipio y colonia.

    Raises:
        HTTPException: 502/504 según fallo REPD.
    """

    etiqueta_municipio = municipio_nombre.strip() if municipio_nombre and municipio_nombre.strip() else str(municipio_id)

    try:
        raw = _repd_client.fetch_cedulas(estado, municipio_id)
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
        municipio=etiqueta_municipio,
        colonia=colonia_resp,
    )
