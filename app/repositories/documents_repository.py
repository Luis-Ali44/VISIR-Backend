from typing import Any
from uuid import uuid4

from app.core.database import supabase


def save_document_storage(
    id_usuario: str, contenido_archivo: bytes, nombre_archivo: str, tipo_archivo: str
) -> str:
    extension = nombre_archivo.split(".")[-1]
    ruta_archivo = f"usuarios/{id_usuario}/documentos/{uuid4()}.{extension}"
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


def get_my_documents(
    limit: int, cursor: str | None, id_usuario: str, id_organizacion: str
) -> list[Any]:
    query = (
        supabase.table("documentos")
        .select("*")
        .eq("id_organizacion", id_organizacion)
        .eq("id_usuario", id_usuario)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if cursor:
        query = query.lt("created_at", cursor)
    response = query.execute()
    return list(response.data)


def get_id_categoria(categoria: str = "Sin categoria") -> str | None:
    response = (
        supabase.table("categorias")
        .select("id")
        .ilike("nombre", categoria)
        .maybe_single()
        .execute()
    )

    if response and isinstance(response.data, dict):
        return str(response.data["id"])

    if categoria == "Sin categoria":
        return None

    default_response = (
        supabase.table("categorias")
        .select("id")
        .ilike("nombre", "Sin categoria")
        .maybe_single()
        .execute()
    )

    if default_response and isinstance(default_response.data, dict):
        return str(default_response.data["id"])
    return None


def save_extracciones_repository(data: list[dict[str, Any]]) -> list[Any]:
    response = supabase.table("extracciones").insert(data).execute()
    return list(response.data)


def tipo_comprobante(tipo: str) -> str | None:
    if not tipo:
        return None
    try:
        response = (
            supabase.table("tipos_comprobantes")
            .select("nombre")
            .eq("clave", str(tipo).strip().upper())
            .maybe_single()
            .execute()
        )
        if response and isinstance(response.data, dict):
            return str(response.data.get("nombre"))
    except Exception:
        print(f"Error al obtener tipo_comprobante para clave: {tipo}")
    return None


def nombre_forma_pago(forma_pago: str) -> str | None:
    if not forma_pago:
        return None
    try:
        clave = int(str(forma_pago).strip())
    except (TypeError, ValueError):
        return None
    try:
        response = (
            supabase.table("formas_pago")
            .select("nombre")
            .eq("clave", clave)
            .maybe_single()
            .execute()
        )
        if response and isinstance(response.data, dict):
            return str(response.data.get("nombre"))
    except Exception:
        return None
    return None