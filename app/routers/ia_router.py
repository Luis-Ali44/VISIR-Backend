import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.schemas.consulta import TokenUsage
from app.core.dependencies import get_user
from app.core.logging import get_logger
from app.schemas.consulta import (
    BusquedaSemanticaRequest,
    BusquedaSemanticaResponse,
    ChunkInfo,
    ConsultaRequest,
    ConsultaResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    TokenUsage,
)

from app.schemas.user_schema import UsuarioActual
from app.services.rag_service import RAGService

router = APIRouter(dependencies=[Depends(get_user)])   # 🔒 toda la ruta requiere auth
logger = get_logger()


def _get_rag_service(request: Request) -> RAGService:
    service = getattr(request.app.state, "rag_service", None)
    if service is None:
        detail = getattr(request.app.state, "rag_service_error", "Servicio RAG no disponible")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    return service



@router.post(
    "/preguntar",
    response_model=ConsultaResponse,
    summary="Consulta semántica sobre documentos fiscales",
    description=(
        "Recupera fragmentos relevantes de ChromaDB y genera una respuesta "
        "con LangChain + LLM OpenAI-compatible. **Requiere token JWT.**"
    ),
)
def preguntar(
    body: ConsultaRequest,
    request: Request,
    usuario: UsuarioActual = Depends(get_user),
) -> ConsultaResponse:
    solicitud_id = str(uuid.uuid4())
    t_inicio = time.perf_counter()
    rag_service = _get_rag_service(request)


    t0 = time.perf_counter()
    try:
        fragmentos = rag_service.retriever.retrieve(
            query=body.pregunta,
            top_k=body.top_k,
            rerank_by_importance=True,
        )
    except RuntimeError as exc:
        msg = str(exc).lower()
        code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if ("embedding" in msg or "conexión" in msg or "timeout" in msg)
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=code, detail="Servicio de recuperación no disponible"
        ) from exc

    lat_recuperacion = round((time.perf_counter() - t0) * 1000, 4)


    t1 = time.perf_counter()
    try:
        resultado = rag_service.chain.invoke(pregunta=body.pregunta, fragmentos=fragmentos)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al generar respuesta: {exc}",
        ) from exc

    lat_generacion = round((time.perf_counter() - t1) * 1000, 4)
    lat_total = round((time.perf_counter() - t_inicio) * 1000, 4)

    chunks_out = [
        ChunkInfo(
            chunk_id=ctx.chunk_id,
            fuente=ctx.filename,
            seccion=ctx.section,
            pagina=ctx.page_number,
            similitud=round(ctx.similarity, 4),
        )
        for ctx in fragmentos
    ]
    latencias = {
        "recuperacion_ms": lat_recuperacion,
        "generacion_ms": lat_generacion,
        "total_ms": lat_total,
    }

    logger.info(
        "solicitud_completada",
        extra={
            "data": {
                "solicitud_id": solicitud_id,
                "usuario_id": usuario.id,
                "pregunta": body.pregunta[:200],
                "chunks_recuperados": [c.chunk_id for c in chunks_out],
                "respuesta_preview": resultado.texto[:100],
                "tiene_cobertura": resultado.tiene_cobertura,
                "latencias_ms": latencias,
            }
        },
    )

    return ConsultaResponse(
        solicitud_id=solicitud_id,
        respuesta=resultado.texto,
        tiene_cobertura=resultado.tiene_cobertura,
        fuentes_citadas=resultado.fuentes_citadas,
        chunks_recuperados=chunks_out,
        fuentes=sorted({ctx.filename for ctx in fragmentos}),
        latencias_ms=latencias,
        tokens=TokenUsage(
            tokens_entrada=resultado.tokens_entrada,
            tokens_salida=resultado.tokens_salida,
        ),
    )



@router.post(
    "/embeddings",
    response_model=EmbeddingResponse,
    summary="Obtener el vector embedding de un texto",
    description=(
        "Devuelve el vector de embeddings generado por el modelo configurado. "
        "Útil para depuración o búsquedas externas. **Requiere token JWT.**"
    ),
)
def obtener_embedding(
    body: EmbeddingRequest,
    request: Request,
    _usuario: UsuarioActual = Depends(get_user),
) -> EmbeddingResponse:
    rag_service = _get_rag_service(request)
    try:
        vector = rag_service.retriever.query_embed_model.get_query_embedding(body.texto)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error al generar embedding: {exc}",
        ) from exc

    return EmbeddingResponse(
        texto=body.texto,
        modelo=rag_service.retriever.config.embedding_model_name,
        dimensiones=len(vector),
        vector=vector,
    )



@router.post(
    "/embeddings/buscar",
    response_model=BusquedaSemanticaResponse,
    summary="Búsqueda semántica sin generación LLM",
    description=(
        "Recupera los fragmentos más similares de ChromaDB sin pasar por el LLM. "
        "Ideal para explorar el corpus o depurar el retriever. **Requiere token JWT.**"
    ),
)
def buscar_semantico(
    body: BusquedaSemanticaRequest,
    request: Request,
    _usuario: UsuarioActual = Depends(get_user),
) -> BusquedaSemanticaResponse:
    rag_service = _get_rag_service(request)

    try:
        fragmentos = rag_service.retriever.retrieve(
            query=body.texto,
            top_k=body.top_k,
            rerank_by_importance=body.rerank,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error en búsqueda semántica: {exc}",
        ) from exc

    return BusquedaSemanticaResponse(
        texto_consulta=body.texto,
        resultados=[
            ChunkInfo(
                chunk_id=ctx.chunk_id,
                fuente=ctx.filename,
                seccion=ctx.section,
                pagina=ctx.page_number,
                similitud=round(ctx.similarity, 4),
            )
            for ctx in fragmentos
        ],
        total=len(fragmentos),
    )