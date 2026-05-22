from typing import Any
from uuid import uuid4

from app.core.database import supabase


def save_document_storage(contenido_archivo: bytes, nombre_archivo: str, tipo_archivo: str) -> str:
    nombre_original = nombre_archivo or "archivo"
    nombre_unico = f"{uuid4()}-{nombre_original}"

    supabase.storage.from_("documentos").upload(
        path=nombre_unico, file=contenido_archivo, file_options={"content-type": tipo_archivo}
    )
    return nombre_unico


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
