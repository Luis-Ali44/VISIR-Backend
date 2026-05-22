from typing import Any

from fastapi import APIRouter, File, Query, UploadFile

from app.services.documents_service import (
    get_document_id,
    get_documents_service,
    subir_documento_service,
)

router = APIRouter(
    prefix="/v1/documentos",
    tags=["Documentos"],
)


@router.post("/cargar")
async def upload_document(file: UploadFile = File(...)) -> dict[str, object]:
    return await subir_documento_service(file)


@router.get("/id")
async def get_document(document_id: str) -> list[Any]:

    return get_document_id(document_id)


@router.get("")
async def get_documents(
    limit: int = Query(10, ge=1, le=50),
    cursor: str | None = None,
) -> dict[str, object]:
    return get_documents_service(
        limit=limit,
        cursor=cursor,
    )
