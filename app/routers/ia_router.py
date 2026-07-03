# app/routers/ia_router.py
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.dependencies import get_user
from app.schemas.user_schema import UsuarioActual
from app.schemas.consulta import ConsultaRequest, ConsultaResponse, FuenteCitada
from app.services.rag_service import RAGServiceLangGraph

router = APIRouter(prefix="/v1/consultas", tags=["consultas-ia"])


_DEFAULT_COVERAGE_THRESHOLD = 0.35
_COVERAGE_THRESHOLD = float(os.getenv("RAG_COVERAGE_THRESHOLD", str(_DEFAULT_COVERAGE_THRESHOLD)))


def get_rag_service(request: Request) -> RAGServiceLangGraph:
    service = getattr(request.app.state, "rag_service", None)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAGService no inicializado en la aplicación",
        )
    return service


def _calcular_cobertura(fuentes: list[dict]) -> bool:
    return any(f.get("similarity", 0.0) >= _COVERAGE_THRESHOLD for f in fuentes)


def _construir_fuentes(fuentes_raw: list[dict]) -> list[FuenteCitada]:

    resultado = []
    for f in fuentes_raw:
        try:
            resultado.append(
                FuenteCitada(
                    filename=f.get("filename", ""),
                    chunk_id=f.get("chunk_id", ""),
                    section=f.get("section", "sin_sección"),
                    page_number=f.get("page_number"),
                    similarity=round(float(f.get("similarity", 0.0)), 4),
                    origen=f.get("origen", "ley"),
                )
            )
        except Exception:

            continue
    return resultado


@router.post("/preguntar", response_model=ConsultaResponse)
def procesar_pregunta_ia(
    body: ConsultaRequest,
    usuario: UsuarioActual = Depends(get_user),
    rag_service: RAGServiceLangGraph = Depends(get_rag_service),
) -> ConsultaResponse:
    solicitud_id = str(uuid.uuid4())

    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no está vinculado a ninguna organización fiscal activa.",
        )

    try:
        respuesta, ruta, metadata = rag_service.ejecutar_consulta(
            pregunta=body.pregunta,
            usuario_id=usuario.id,
            id_organizacion=usuario.id_organizacion,
            top_k=body.top_k,
        )

        fuentes_raw: list[dict] = metadata.get("fuentes_recuperadas", [])
        fuentes_citadas = _construir_fuentes(fuentes_raw)
        tiene_cobertura = _calcular_cobertura(fuentes_raw)

        return ConsultaResponse(
            solicitud_id=solicitud_id,
            respuesta=respuesta,
            tiene_cobertura=tiene_cobertura,
            fuentes_citadas=fuentes_citadas,
            latencias_ms={"grafo_total": metadata["latencia_ms"]},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la máquina de estados VISIR: {str(e)}",
        )
