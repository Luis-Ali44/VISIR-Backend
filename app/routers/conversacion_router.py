from fastapi import APIRouter, Depends

from app.core.dependencies import get_user
from app.schemas.conversacion_schema import ConsultaRequest, ConsultaResponse
from app.schemas.user_schema import UsuarioActual
from app.services.conversacion_service import consultar_service

router = APIRouter(prefix="/v1/consultas", tags=["consultas"], dependencies=[Depends(get_user)])


@router.post("/consultar", response_model=ConsultaResponse)
async def consultar_router(
    body: ConsultaRequest, user: UsuarioActual = Depends(get_user)
) -> ConsultaResponse:
    return await consultar_service(pregunta=body.pregunta, user=user)
