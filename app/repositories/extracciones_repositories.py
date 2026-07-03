from datetime import date
from typing import Any

from app.core.database import supabase


def get_extraccion_by_id(extraccion_id: str) -> list[Any]:
    response = supabase.table("extracciones").select("*").eq("id", extraccion_id).execute()
    return list(response.data)


def get_extracciones_repository(
    limit: int,
    cursor: str | None = None,
    fecha_inicio: date | None = None,
    fecha_final: date | None = None,
    rfc_emisor: str | None = None,
    rfc_receptor: str | None = None,
    tipo_comprobante: str | None = None,
    estado: str | None = None,
) -> list[Any]:

    query = supabase.table("extracciones").select("*").order("created_at", desc=True).limit(limit)
    if cursor:
        query = query.lt("created_at", cursor)

    if fecha_inicio and fecha_final:
        query = query.gte("created_at", fecha_inicio.isoformat()).lte(
            "created_at", fecha_final.isoformat()
        )

    if rfc_emisor:
        query = query.eq("rfc_emisor", rfc_emisor)

    if rfc_receptor:
        query = query.eq("rfc_receptor", rfc_receptor)

    if tipo_comprobante:
        query = query.eq("tipo_comprobante", tipo_comprobante)

    if estado:
        query = query.eq("estado", estado)

    response = query.execute()
    return list(response.data)
