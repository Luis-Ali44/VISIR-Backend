from datetime import date
from typing import Any

from fastapi import HTTPException

from app.repositories.extracciones_repository import (
    get_extraccion_by_id,
)
from app.repositories.extracciones_repository import (
    get_extracciones_by_org as get_extracciones_repository,
)


def get_extraccion_by_id_service(extraccion_id: str, id_organizacion: str) -> list[Any]:
    extraccion = get_extraccion_by_id(extraccion_id, id_organizacion=id_organizacion)

    if not extraccion:
        raise HTTPException(status_code=404, detail="Extracción no encontrada")
    return list(extraccion)


def get_extracciones_service(
    limit: int,
    cursor: str | None,
    fecha_inicio: date | None = None,
    fecha_final: date | None = None,
    rfc_emisor: str | None = None,
    rfc_receptor: str | None = None,
    tipo_comprobante: str | None = None,
    estado: str | None = None,
) -> dict[str, object]:

    extracciones = get_extracciones_repository(
        limit=limit,
        cursor=cursor,
        fecha_inicio=fecha_inicio,
        fecha_final=fecha_final,
        rfc_emisor=rfc_emisor,
        rfc_receptor=rfc_receptor,
        tipo_comprobante=tipo_comprobante,
        estado=estado,
    )

    next_cursor = None
    if extracciones:
        next_cursor = extracciones[-1]["created_at"]

    return {
        "data": extracciones,
        "next_cursor": next_cursor,
    }
