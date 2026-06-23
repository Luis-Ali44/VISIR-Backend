# app/routers/ia_router.py
import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.dependencies import get_user
from app.schemas.user_schema import UsuarioActual
from app.schemas.consulta import ConsultaRequest, ConsultaResponse
from app.services.rag_service import RAGServiceLangGraph

router = APIRouter(prefix="/v1/consultas", tags=["consultas-ia"])

def get_rag_service(request: Request) -> RAGServiceLangGraph:
    service = getattr(request.app.state, "rag_service", None)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAGService no inicializado en la aplicación"
        )
    return service

@router.post("/preguntar", response_model=ConsultaResponse)
def procesar_pregunta_ia(
    body: ConsultaRequest,
    usuario: UsuarioActual = Depends(get_user),
    rag_service: RAGServiceLangGraph = Depends(get_rag_service)
):
    solicitud_id = str(uuid.uuid4())

    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no está vinculado a ninguna organización fiscal activa."
        )

    try:
        # Ejecutar la consulta en la máquina de estados aplanada
        respuesta, ruta, metadata = rag_service.ejecutar_consulta(
            pregunta=body.pregunta,
            usuario_id=usuario.id,
            id_organizacion=usuario.id_organizacion,
            top_k=body.top_k
        )

        return ConsultaResponse(
            solicitud_id=solicitud_id,
            respuesta=respuesta,
            tiene_cobertura=True,
            fuentes_citadas=metadata.get("palabras_clave", []),
            latencias_ms={"grafo_total": metadata["latencia_ms"]},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la máquina de estados VISIR: {str(e)}"
        )
