from typing import Any

from app.core.database import supabase


def get_extraccion_by_id(extraccion_id: str) -> list[Any]:
    response = supabase.table("extracciones").select("*").eq("id", extraccion_id).execute()
    return list(response.data)


def get_extracciones_repository(limit=int, cursor=str | None) -> list[Any]:
    query = supabase.table("extracciones").select("*").order("created_at", desc=True).limit(limit)
    if cursor:
        query = query.lt("created_at", cursor)
    response = query.execute()
    return list(response.data)
