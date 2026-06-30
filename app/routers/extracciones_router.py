from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_user
from app.schemas.extraccion import ExtraccionResponse
from app.schemas.user_schema import UsuarioActual
from app.services.extracciones_service import get_extraccion_by_id_service, get_extracciones_service

router = APIRouter(
    prefix="/v1/Extracciones", tags=["Extracciones"], dependencies=[Depends(get_user)]
)


@router.get("/{extraccion_id}", response_model=list[ExtraccionResponse])
async def get_extraccion_by_id_router(
    extraccion_id: str, usuario: UsuarioActual = Depends(get_user)
) -> list[Any]:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no está vinculado a ninguna organización.",
        )
    return get_extraccion_by_id_service(extraccion_id, id_organizacion=usuario.id_organizacion)


@router.get("", response_model=dict[str, object])
async def get_extracciones(
    limit: int = Query(10, ge=1, le=50),
    cursor: str | None = None,
    usuario: UsuarioActual = Depends(get_user),
) -> dict[str, object]:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no está vinculado a ninguna organización.",
        )
    return get_extracciones_service(
        limit=limit, cursor=cursor, id_organizacion=usuario.id_organizacion
    )
