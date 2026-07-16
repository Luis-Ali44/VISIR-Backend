import os
import uuid

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import get_user
from app.repositories.conversaciones_repository import guardar_turno, obtener_historial
from app.schemas.consulta import ConsultaRequest, ConsultaResponse, FuenteCitada
from app.schemas.user_schema import UsuarioActual
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
    return cast(RAGServiceLangGraph, service)


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
        historial = obtener_historial(usuario.id, usuario.id_organizacion)

        respuesta, _ruta, metadata = rag_service.ejecutar_consulta(
            pregunta=body.pregunta,
            usuario_id=usuario.id,
            id_organizacion=usuario.id_organizacion,
            top_k=body.top_k,
            historial=historial,
        )

        guardar_turno(
            id_usuario=usuario.id,
            id_organizacion=usuario.id_organizacion,
            mensaje_usuario=body.pregunta,
            respuesta_sistema=respuesta,
        )

        fuentes_raw: list[dict] = metadata.get("fuentes_recuperadas", [])
        fuentes_citadas = _construir_fuentes(fuentes_raw)
        tiene_cobertura_heuristico = _calcular_cobertura(fuentes_raw)
        tiene_cobertura_llm = metadata.get("tiene_cobertura")
        tiene_cobertura = (
            tiene_cobertura_llm
            if isinstance(tiene_cobertura_llm, bool)
            else tiene_cobertura_heuristico
        )

        return ConsultaResponse(
            solicitud_id=solicitud_id,
            respuesta=respuesta,
            tiene_cobertura=tiene_cobertura,
            confianza_score=metadata.get("confianza_score"),
            accion_seleccionada=metadata.get("accion_seleccionada"),
            fuentes_citadas=fuentes_citadas,
            latencias_ms={"grafo_total": metadata["latencia_ms"]},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la máquina de estados VISIR: {e!s}",
        ) from e
