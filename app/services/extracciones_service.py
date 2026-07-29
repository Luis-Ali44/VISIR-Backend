from datetime import date
from typing import Any

from fastapi import HTTPException


from app.core.database import ExecCtx
from app.repositories.extracciones_repositories import ExtraccionesRepository
from app.schemas.user_schema import UsuarioActual


def get_extraccion_by_id_service(extraccion_id: str, usuario: UsuarioActual) -> list[Any]:
    repo = ExtraccionesRepository(usuario)
    extraccion = repo.get_extraccion_by_id(extraccion_id)

    if not extraccion:
        raise HTTPException(status_code=404, detail="Extracción no encontrada")
    return list(extraccion)


def get_extracciones_service(
    limit: int,
    cursor: str | None,
    usuario:UsuarioActual,
    id_organizacion: str | None,
    fecha_inicio: date | None = None,
    fecha_final: date | None = None,
    rfc_emisor: str | None = None,
    rfc_receptor: str | None = None,
    tipo_comprobante: str | None = None,
    estado: str | None = None,
) -> dict[str, object]:

    if not usuario.id_organizacion:
        raise HTTPException(    
            status_code=400, detail="El usuario no está registrado en ninguna organización"
        )

    repo = ExtraccionesRepository(usuario)

    extracciones = repo.get_extracciones_repository(
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

    next_cursor = None
    if extracciones:
        next_cursor = extracciones[-1]["created_at"]

    return {
        "data": extracciones,
        "next_cursor": next_cursor,
    }
