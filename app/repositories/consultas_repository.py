from typing import Any, cast

from app.core.database import supabase


def gasto_provedor() -> list[dict[str, Any]]:
    response = (
        supabase.table("extracciones")
        .select("rfc_emisor, nombre_emisor, total.sum(), id.count()")
        .eq("estado", "procesado")
        .execute()
    )

    return cast(list[dict[str, Any]], response.data)


def gasto_categoria() -> list[dict[str, Any]]:
    response = (
        supabase.table("extracciones")
        .select("id_categorias,total.sum(), id.count()")
        .eq("estado", "procesado")
        .execute()
    )

    return cast(list[dict[str, Any]], response.data)
