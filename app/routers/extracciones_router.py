from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_user
from app.schemas.extraccion import ExtraccionesPaginadasResponse, ExtraccionResponse
from app.schemas.user_schema import UsuarioActual
from app.services.extracciones_service import get_extraccion_by_id_service, get_extracciones_service

router = APIRouter(prefix="/v1/Extracciones", tags=["Extracciones"])


@router.get("", response_model=ExtraccionesPaginadasResponse)
async def get_extracciones(
    usuario: UsuarioActual = Depends(get_user),
    limit: int = Query(10, ge=1, le=50),
    cursor: str | None = None,
    id_organizacion: str | None = None,
    fecha_inicio: date | None = None,
    fecha_final: date | None = None,
    rfc_emisor: str | None = None,
    rfc_receptor: str | None = None,
    tipo_comprobante: str | None = None,
    estado: str | None = None,
) -> ExtraccionesPaginadasResponse:
    return get_extracciones_service(
        usuario=usuario,
        limit=limit,
        cursor=cursor,
        id_organizacion=id_organizacion,
        fecha_inicio=fecha_inicio,
        fecha_final=fecha_final,
        rfc_emisor=rfc_emisor,
        rfc_receptor=rfc_receptor,
        tipo_comprobante=tipo_comprobante,
        estado=estado,
    )


@router.get("/{extraccion_id}", response_model=ExtraccionResponse)
async def get_extraccion_by_id_router(
    extraccion_id: str,
    usuario: UsuarioActual = Depends(get_user),
) -> ExtraccionResponse:
    return get_extraccion_by_id_service(extraccion_id, usuario=usuario)
