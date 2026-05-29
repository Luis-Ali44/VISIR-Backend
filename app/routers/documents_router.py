from typing import Any

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.auth import get_current_user
from app.schemas.documents_schema import DocumentResponse
from app.services.documents_service import (
    get_document_id,
    get_documents_service,
    subir_documento_service,
)

router = APIRouter(
    prefix="/v1/documentos", tags=["Documentos"], dependencies=[Depends(get_current_user)]
)


@router.post("/cargar", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
) -> DocumentResponse:
    return await subir_documento_service(file, current_user)


@router.get("/id", response_model=list[DocumentResponse])
async def get_document(document_id: str) -> list[Any]:
    return get_document_id(document_id)


@router.get("", response_model=dict[str, object])
async def get_documents(
    limit: int = Query(10, ge=1, le=50),
    cursor: str | None = None,
) -> dict[str, object]:
    return get_documents_service(limit=limit, cursor=cursor)
