import asyncio
import os
import sys

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.dependencies import get_user
from app.core.logging import get_logger
from app.schemas.ingest import IngestStatusResponse
from app.schemas.user_schema import UsuarioActual

router = APIRouter(prefix="/v1/ingest", tags=["ingesta"], dependencies=[Depends(get_user)])
logger = get_logger()

_ingest_running: bool = False


def _get_chroma_env() -> tuple[str, str]:
    """
    Lee CHROMA_PATH / CHROMA_COLLECTION directo de variables de entorno,
    igual que hace rag/config.py::load_config_from_env. app/core/config.py
    no expone get_settings() ni estos campos, así que no se usa aquí.
    """
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    chroma_collection = os.getenv("CHROMA_COLLECTION", "documentos_fiscales")
    return chroma_path, chroma_collection


def _get_chroma_org_env() -> tuple[str, str]:
    """
    Igual que _get_chroma_env(), pero para la colección compartida de
    documentos/CFDIs de organización (CHROMA_ORG_COLLECTION), separada
    de la normativa SAT (CHROMA_COLLECTION). Ver rag/config.py.
    """
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    chroma_org_collection = os.getenv("CHROMA_ORG_COLLECTION", "documentos_organizacion")
    return chroma_path, chroma_org_collection


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
    chroma_path, chroma_collection = _get_chroma_env()
    background_tasks.add_task(
        _run_ingestion_background,
        chroma_path=chroma_path,
        collection=chroma_collection,
    )
    logger.info("ingesta_iniciada")
    return IngestStatusResponse(status="iniciada", mensaje="Ingesta lanzada en background.")


@router.get(
    "/stats",
    summary="Estadísticas de ChromaDB — normativa SAT",
    description=(
        "Devuelve chunks indexados y documentos únicos de la colección "
        "de normativa SAT (CHROMA_COLLECTION), compartida entre todas las "
        "organizaciones. NO incluye los CFDIs/documentos subidos por "
        "ninguna organización — para eso, ver /v1/ingest/org-stats. "
        "**Requiere token JWT.**"
    ),
)
def get_stats(_usuario: UsuarioActual = Depends(get_user)) -> dict:
    from rag.store import FiscalChromaStore
    chroma_path, chroma_collection = _get_chroma_env()
    try:
        store = FiscalChromaStore(
            chroma_path=chroma_path,
            collection_name=chroma_collection,
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


@router.get(
    "/org-stats",
    summary="Estadísticas de ChromaDB — documentos de tu organización",
    description=(
        "Devuelve chunks indexados y documentos únicos de la colección "
        "compartida de organización (CHROMA_ORG_COLLECTION), acotado "
        "SOLO a la organización del usuario autenticado — nunca al total "
        "de todas las organizaciones. Incluye CFDIs y documentos "
        "generales subidos vía /v1/documentos/cargar. **Requiere token JWT.**"
    ),
)
def get_org_stats(usuario: UsuarioActual = Depends(get_user)) -> dict:
    from rag.store import FiscalChromaStore

    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no está vinculado a ninguna organización.",
        )

    chroma_path, chroma_org_collection = _get_chroma_org_env()
    try:
        store = FiscalChromaStore(
            chroma_path=chroma_path,
            collection_name=chroma_org_collection,
        )
        return store.stats_by_org(id_organizacion=usuario.id_organizacion)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo conectar a ChromaDB: {exc}",
        ) from exc