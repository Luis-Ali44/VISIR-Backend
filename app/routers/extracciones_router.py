from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_user
from app.schemas.extraccion import ExtraccionResponse
from app.services.extracciones_service import get_extraccion_by_id_service, get_extracciones_service

router = APIRouter(
    prefix="/v1/Extracciones", tags=["Extracciones"], dependencies=[Depends(get_user)]
)


@router.get("/{extraccion_id}", response_model=list[ExtraccionResponse])
async def get_extraccion_by_id_router(extraccion_id: str) -> list[Any]:
    return get_extraccion_by_id_service(extraccion_id)


@router.get("", response_model=dict[str, object])
async def get_extracciones(
    limit: int = Query(10, ge=1, le=50),
    cursor: str | None = None,
) -> dict[str, object]:
    return get_extracciones_service(limit=limit, cursor=cursor)
