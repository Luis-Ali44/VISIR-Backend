from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile

from app.repositories.documents_repository import (
    get_document_by_id,
    get_documents_repository,
    get_id_categoria,
    get_my_documents,
    save_document_metadata,
    save_document_storage,
)
from app.schemas.documents_schema import DocumentCreate, DocumentResponse
from app.schemas.user_schema import UsuarioActual

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = ["application/pdf", "text/xml", "application/xml"]


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


async def subir_documento_service(archivo: UploadFile, user: UsuarioActual) -> DocumentResponse:

    id_usuario = user.id
    id_organizacion = user.id_organizacion

    contenido = await validate_document(archivo)

    tipo_archivo = archivo.content_type

    if tipo_archivo is None:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo inválido",
        )

    ruta_archivo = save_document_storage(
        id_usuario=id_usuario,
        contenido_archivo=contenido,
        nombre_archivo=archivo.filename or "archivo",
        tipo_archivo=tipo_archivo,
    )

    categoria = get_id_categoria()

    id_categoria = UUID(categoria) if categoria else None

    metadata = DocumentCreate(
        nombre=archivo.filename or "archivo",
        tipo=tipo_archivo,
        tamaño=len(contenido),
        link=ruta_archivo,
        id_usuario=UUID(id_usuario),
        id_organizacion=UUID(id_organizacion),
        id_categorias=id_categoria,
    )

    resultado = save_document_metadata(
        metadata.model_dump(mode="json")
    )  # Maneja el UUID como str para que no de error

    return DocumentResponse(**resultado[0])


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


def get_my_documents_service(
    limit: int, cursor: str | None, usuario_actual: UsuarioActual
) -> dict[str, object]:
    id_usuario = usuario_actual.id
    id_organizacion = usuario_actual.id_organizacion

    if not id_organizacion:
        raise HTTPException(
            status_code=400, detail="El usuario no esta registrado en ninguna organizacion"
        )

    documentos = get_my_documents(
        limit=limit, cursor=cursor, id_usuario=id_usuario, id_organizacion=id_organizacion
    )

    next_cursor = None
    if documentos:
        next_cursor = documentos[-1]["created_at"]
    return {"data": documentos, "next_cursor": next_cursor}
