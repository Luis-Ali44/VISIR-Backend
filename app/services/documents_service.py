import hashlib
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile

from app.repositories.documents_repository import DocumentRepository
from app.schemas.documents_schema import (
    DocumentCreate,
    DocumentoFallido,
    DocumentResponse,
    LoteResponse,
)
from app.schemas.user_schema import UsuarioActual

# Conexion de paola
from app.services.helper import (
    verificar_xml,
)
from app.tasks.document_tasks import iniciar_procesamiento

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/xml": ".xml",
    "application/xml": ".xml",
    "image/jpeg": ".jpeg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/bmp": ".bmp",
    "image/webp": ".webp",
}


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
    nombre_archivo = archivo.filename or "archivo"
    repo = DocumentRepository(user)

    if not id_usuario or not id_organizacion:
        raise HTTPException(status_code=400, detail="Usuario u organización inválidos")

    contenido = await validate_document(archivo)

    hash_archivo = hashlib.sha256(contenido).hexdigest()

    duplicados = repo.get_document_by_hash(hash_archivo)

    if duplicados:
        raise HTTPException(
            status_code=409,
            detail="Este archivo ya fue subido antes",
        )

    if nombre_archivo:
        extencion = nombre_archivo.split(".")[-1].lower()

    if extencion == "xml":
        es_valido, errores = verificar_xml(contenido)
        if not es_valido:
            raise HTTPException(status_code=400, detail=f"XML no válido: {', '.join(errores)}")

    tipo_archivo = archivo.content_type

    if tipo_archivo is None:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo inválido",
        )

    # Guardar el archivo en el almacenamiento y obtener la ruta
    try:
        ruta_archivo = repo.save_document_storage(
            contenido_archivo=contenido,
            nombre_archivo=nombre_archivo,
            tipo_archivo=tipo_archivo,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="No se pudo guardar el archivo en storage"
        ) from exc

    if not ruta_archivo:
        raise HTTPException(status_code=500, detail="No se obtuvo la ruta del archivo guardado")

    # Crear metadata del documento
    # Categoria se deja fuera del flujo por ahora; se activará cuando el OCR la devuelva.
    metadata = DocumentCreate(
        nombre=nombre_archivo,
        tipo=tipo_archivo,
        tamaño=len(contenido),
        link=ruta_archivo,
        id_usuario=UUID(id_usuario),
        id_organizacion=UUID(id_organizacion),
        # id_categorias=id_categoria,
        id_categorias=None,
        hash_archivo=hash_archivo,  # Se puede calcular un hash si es necesario
        estado_documento="procesando",
    )

    # Guardar metadata en la base de datos
    try:
        resultado = repo.save_document_metadata(
            metadata.model_dump(mode="json")
        )  # Maneja el UUID como str para que no de error

    except Exception as exc:
        repo.delete_document_storage(ruta_archivo)  # Eliminar el archivo si falla la metadata
        raise HTTPException(
            status_code=500, detail=f"No se pudieron guardar los metadatos del documento {exc}"
        ) from exc

    if not isinstance(resultado, list) or not resultado or not isinstance(resultado[0], dict):
        raise HTTPException(
            status_code=500,
            detail="La metadata fue guardada pero la respuesta no tiene el formato esperado",
        )

    # Obtenemos id_documento de la metadata guardada para relacionarlo con las extracciones
    id_documento = resultado[0]["id"]
    # Aqui pasamos a celery
    iniciar_procesamiento.delay(
        id_documento=id_documento,
        id_organizacion=id_organizacion,
        id_usuario=id_usuario,
        ruta_archivo=ruta_archivo,
        nombre_archivo=nombre_archivo,
    )

    return DocumentResponse(**resultado[0])


def get_document_id(document_id: str, user: UsuarioActual) -> list[Any]:

    repo = DocumentRepository(user)
    documento = repo.get_document_by_id(document_id)

    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return list(documento)


def get_documents_service(
    limit: int,
    user: UsuarioActual,
    cursor: str | None = None,
) -> dict[str, object]:
    repo = DocumentRepository(user)
    documentos = repo.get_documents_repository(limit=limit, cursor=cursor)

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
    repo = DocumentRepository(usuario_actual)
    documentos = repo.get_my_documents(
        limit=limit, cursor=cursor, id_usuario=id_usuario, id_organizacion=id_organizacion
    )

    next_cursor = None
    if documentos:
        next_cursor = documentos[-1]["created_at"]
    return {"data": documentos, "next_cursor": next_cursor}


async def subir_lote_service(files: list[UploadFile], user: UsuarioActual) -> LoteResponse:
    exitosos: list[DocumentResponse] = []
    fallidos: list[DocumentoFallido] = []
    # Nombre del archivo actual

    for file in files:
        nombre_archivo = file.filename or "archivo"
        try:
            result = await subir_documento_service(file, user)
            exitosos.append(result)
            print(f"Archivo {nombre_archivo} procesado exitosamente.")

        except HTTPException as exc:
            fallidos.append(DocumentoFallido(nombre_archivo=nombre_archivo, error=exc.detail))
            print(f"Error al procesar el archivo {nombre_archivo}: {exc.detail}")

    return LoteResponse(exitosos=exitosos, fallidos=fallidos)
