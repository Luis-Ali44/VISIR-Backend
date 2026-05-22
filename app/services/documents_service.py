from typing import Any

from fastapi import HTTPException, UploadFile

from app.repositories.documents_repository import (
    get_document_by_id,
    get_documents_repository,
    save_document_metadata,
    save_document_storage,
)

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = [
    "application/pdf",
    "text/xml",
]


async def validate_document(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Archivo demasiado grande",
        )

    await file.seek(0)

    return content


async def subir_documento_service(
    archivo: UploadFile,
) -> dict[str, object]:
    contenido = await validate_document(archivo)

    nombre_guardado = save_document_storage(
        contenido_archivo=contenido,
        nombre_archivo=archivo.filename or "archivo",
        tipo_archivo=archivo.content_type or "application/octet-stream",
    )

    metadata = {
        "nombre": archivo.filename,
        "tipo": archivo.content_type,
        "tamano": len(contenido),
        "url": nombre_guardado,
    }

    save_document_metadata(metadata)

    return {
        "messege": "archivo guardado",
        "archivo guardado": nombre_guardado,
        "metadata": metadata,
    }


def get_document_id(document_id: str) -> list[Any]:

    documento = get_document_by_id(document_id)

    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return list(documento)


def get_documents_service(
    limit: int,
    cursor: str | None = None,
) -> dict[str, object]:
    documentos = get_documents_repository(limit=limit, cursor=cursor)

    next_cursor = None

    if documentos:
        next_cursor = documentos[-1]["created_at"]

    return {
        "data": documentos,
        "next_cursor": next_cursor,
    }
