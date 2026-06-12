import asyncio
import sys

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.core.config import get_settings
from app.core.dependencies import get_user
from app.core.logging import get_logger
from app.schemas.ingest import IngestStatusResponse
from app.schemas.user_schema import UsuarioActual

router = APIRouter(dependencies=[Depends(get_user)])  
logger = get_logger()

_ingest_running: bool = False


async def _run_ingestion_background(chroma_path: str, collection: str) -> None:
    global _ingest_running
    _ingest_running = True
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ingestion.run",
            "--chroma-path", chroma_path,
            "--collection", collection,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("ingesta_fallida", extra={"data": {"stderr": stderr.decode()[:500]}})
        else:
            logger.info("ingesta_completada", extra={"data": {"stdout": stdout.decode()[:300]}})
    finally:
        _ingest_running = False


@router.post(
    "/run",
    response_model=IngestStatusResponse,
    summary="Lanzar ingesta de PDFs",
    description=(
        "Procesa los PDFs en /data e indexa en ChromaDB. "
        "Solo un proceso a la vez. **Requiere token JWT.**"
    ),
)
def run_ingest(
    background_tasks: BackgroundTasks,
    _usuario: UsuarioActual = Depends(get_user),
) -> IngestStatusResponse:
    global _ingest_running
    if _ingest_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay una ingesta en curso. Espera a que termine.",
        )
    settings = get_settings()
    background_tasks.add_task(
        _run_ingestion_background,
        chroma_path=settings.CHROMA_PATH,
        collection=settings.CHROMA_COLLECTION,
    )
    logger.info("ingesta_iniciada")
    return IngestStatusResponse(status="iniciada", mensaje="Ingesta lanzada en background.")


@router.get(
    "/stats",
    summary="Estadísticas de ChromaDB",
    description="Devuelve chunks indexados y documentos únicos. **Requiere token JWT.**",
)
def get_stats(_usuario: UsuarioActual = Depends(get_user)) -> dict:
    from rag.store import FiscalChromaStore
    settings = get_settings()
    try:
        store = FiscalChromaStore(
            chroma_path=settings.CHROMA_PATH,
            collection_name=settings.CHROMA_COLLECTION,
        )
        stats = store.stats()
        hashes = store.get_indexed_doc_hashes()
        return {
            "collection": stats["collection"],
            "total_chunks": stats["total_chunks"],
            "documentos_unicos": len(hashes),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo conectar a ChromaDB: {exc}",
        ) from exc
