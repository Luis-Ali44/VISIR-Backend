from datetime import date
from typing import Any

from app.core.database import supabase


def get_extraccion_by_id(extraccion_id: str) -> list[Any]:
    response = supabase.table("extracciones").select("*").eq("id", extraccion_id).execute()
    return list(response.data)


def get_extracciones_repository(
    limit: int,
    id_organizacion: str | None,
    cursor: str | None = None,
    fecha_inicio: date | None = None,
    fecha_final: date | None = None,
    rfc_emisor: str | None = None,
    rfc_receptor: str | None = None,
    tipo_comprobante: str | None = None,
    estado: str | None = None,
) -> list[Any]:

    query = supabase.table("extracciones").select("*").limit(limit).order("created_at", desc=True)

    if id_organizacion:
        query = query.eq("id_organizacion", id_organizacion)

    if cursor:
        query = query.lt("created_at", cursor)

    if fecha_inicio:
        query = query.gte("fecha_emision", fecha_inicio.isoformat())

    if fecha_final:
        query = query.lte("fecha_emision", fecha_final.isoformat())

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


def get_estadisticas_basicas(id_organizacion: str, limit: int = 100) -> dict[str, Any]:
    rows = get_extracciones_repository(id_organizacion=id_organizacion, limit=limit)

    if not rows:
        return {
            "total_facturas": 0,
            "gasto_total": 0.0,
            "gasto_promedio": 0.0,
            "proveedores_unicos": 0,
            "periodo_inicio": None,
            "periodo_fin": None,
        }

    gasto_total = sum(float(r.get("total") or 0) for r in rows)
    proveedores = set(r.get("rfc_emisor") for r in rows if r.get("rfc_emisor"))

    fechas = [r.get("fecha_emision") for r in rows if r.get("fecha_emision")]
    periodo_inicio = min(fechas) if fechas else None
    periodo_fin = max(fechas) if fechas else None

    return {
        "total_facturas": len(rows),
        "gasto_total": round(gasto_total, 2),
        "gasto_promedio": round(gasto_total / len(rows), 2) if rows else 0.0,
        "proveedores_unicos": len(proveedores),
        "periodo_inicio": periodo_inicio,
        "periodo_fin": periodo_fin,
    }


def get_resumen_gasto_por_mes(id_organizacion: str) -> dict[str, Any]:

    return {}


def get_gastos_por_proveedor(id_organizacion: str, top_n: int = 5) -> dict[str, Any]:

    return {}


def get_gastos_por_categoria(id_organizacion: str) -> dict[str, Any]:

    return {}
