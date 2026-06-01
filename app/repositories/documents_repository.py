from typing import Any
from uuid import uuid4

from app.core.database import supabase


def save_document_storage(contenido_archivo: bytes, nombre_archivo: str, tipo_archivo: str) -> str:

    extension = nombre_archivo.split(".")[-1]
    ruta_archivo = f"documentos/{uuid4()}.{extension}"
    supabase.storage.from_("documentos").upload(
        path=ruta_archivo, file=contenido_archivo, file_options={"content-type": tipo_archivo}
    )
    return ruta_archivo


def save_document_metadata(data: dict) -> list[Any]:
    response = supabase.table("documentos").insert(data).execute()

    return list(response.data)


def get_document_by_id(documento_id: str) -> list[Any]:
    response = supabase.table("documentos").select().eq("id", documento_id).execute()
    return list(response.data)


def get_documents_repository(limit: int, cursor: str | None = None) -> list[Any]:
    query = supabase.table("documentos").select("*").order("created_at", desc=True).limit(limit)
    if cursor:
        query = query.lt("created_at", cursor)
    response = query.execute()
    return list(response.data)
