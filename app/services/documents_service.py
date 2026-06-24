import asyncio
import tempfile
import traceback
from functools import partial
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile

from app.repositories.documents_repository import (
    get_document_by_id,
    get_documents_repository,
    get_my_documents,
    save_document_metadata,
    save_document_storage,
    save_extracciones_repository,
)
from app.schemas.documents_schema import DocumentCreate, DocumentResponse
from app.schemas.user_schema import UsuarioActual

# Conexion de paola
from app.services.Extraccion.pipeline import procesar
from app.services.helper import get_nombre_forma_pago, map_tipo_comprobante, parse_fecha

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/xml": ".xml",
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

    if not id_usuario or not id_organizacion:
        raise HTTPException(status_code=400, detail="Usuario u organización inválidos")

    contenido = await validate_document(archivo)

    tipo_archivo = archivo.content_type

    if tipo_archivo is None:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo inválido",
        )

    # Guardar el archivo en el almacenamiento y obtener la ruta
    try:
        ruta_archivo = save_document_storage(
            id_usuario=id_usuario,
            contenido_archivo=contenido,
            nombre_archivo=archivo.filename or "archivo",
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
        nombre=archivo.filename or "archivo",
        tipo=tipo_archivo,
        tamaño=len(contenido),
        link=ruta_archivo,
        id_usuario=UUID(id_usuario),
        id_organizacion=UUID(id_organizacion),
        # id_categorias=id_categoria,
        id_categorias=None,
    )

    # Guardar metadata en la base de datos
    try:
        resultado = save_document_metadata(
            metadata.model_dump(mode="json")
        )  # Maneja el UUID como str para que no de error
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="No se pudieron guardar los metadatos del documento"
        ) from exc

    if not isinstance(resultado, list) or not resultado or not isinstance(resultado[0], dict):
        raise HTTPException(
            status_code=500, detail="No se pudo recuperar la metadata guardada del documento"
        )

    ext = Path(archivo.filename or "archivo.pdf").suffix
    tmp_path = None

    # Descargar el archivo para procesarlo con la libreria de paolaG
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contenido)
            tmp_path = Path(tmp.name)

        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, partial(procesar, ruta_archivo=tmp_path, guardar_txt=False)
            )
        except Exception as exc:
            raise HTTPException(
                status_code=422, detail="No se pudo procesar el archivo con OCR"
            ) from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)  # Eliminar el archivo temporal

    # Categoria se mantiene fuera del flujo actual hasta que el OCR la entregue.
    # categoria = get_id_categoria()
    # id_categoria = UUID(categoria) if categoria else None

    # Obtenemos id_documento de la metadata guardada para relacionarlo con las extracciones
    id_documento = resultado[0]["id"]

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("cfdis"), list)
        or not data.get("cfdis")
    ):
        raise HTTPException(status_code=422, detail="No se encontraron CFDIs para extraer")

    rows = []
    for item in data.get("cfdis", []):
        datos = item.get("datos", {}) if isinstance(item, dict) else {}

        forma_pago = datos.get("forma_pago")
        fecha_emision_raw = datos.get("fecha_emision")
        tipo_comprobante_raw = datos.get("tipo_de_comprobante")

    rows.append(
        {
            "folio_fiscal": datos.get("folio_fiscal"),
            "total": datos.get("total"),
            "metadatos": datos,
            "fecha_emision": parse_fecha(str(fecha_emision_raw)).isoformat()
            if fecha_emision_raw is not None
            else None,
            "tipo_comprobante": map_tipo_comprobante(str(tipo_comprobante_raw))
            if tipo_comprobante_raw is not None
            else None,
            "metodo_pago": datos.get("metodo_pago"),
            "estado": "procesado",
            "rfc_emisor": datos.get("emisor", {}).get("RFC"),
            "nombre_emisor": datos.get("emisor", {}).get("nombre"),
            "rfc_receptor": datos.get("receptor", {}).get("RFC"),
            "nombre_receptor": datos.get("receptor", {}).get("nombre"),
            "id_documento": id_documento,
            "id_organizacion": id_organizacion,
            "forma_pago": get_nombre_forma_pago(str(forma_pago)) if forma_pago else None,
        }
    )

    # Guardamos las extracciones en la base de datos
    try:
        save_extracciones_repository(rows)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="No se pudieron guardar las extracciones"
        ) from exc

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


async def subir_lote_service(
    files: list[UploadFile], user: UsuarioActual
) -> list[DocumentResponse]:
    response = []
    for file in files:
        try:
            result = await subir_documento_service(file, user)
            response.append(result)
            print(f"Archivo {file.filename} procesado exitosamente.")

        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=f"Error al procesar el archivo {file.filename}: {exc.detail}",
            ) from exc
    return response
