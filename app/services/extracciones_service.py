from typing import Any

from fastapi import HTTPException

from app.repositories.extracciones_repositories import (
    get_extraccion_by_id,
    get_extracciones_repository,
)


def get_extraccion_by_id_service(extraccion_id: str) -> list[Any]:
    extraccion = get_extraccion_by_id(extraccion_id)

    if not extraccion:
        raise HTTPException(status_code=404, detail="Extracción no encontrada")
    return list(extraccion)


def get_extracciones_service(limit: int, cursor: str | None) -> dict[str, object]:
    extracciones = get_extracciones_repository(limit=limit, cursor=cursor)

    next_cursor = None
    if extracciones:
        next_cursor = extracciones[-1]["created_at"]

    return {
        "data": extracciones,
        "next_cursor": next_cursor,
    }
