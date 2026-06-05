from fastapi import APIRouter

from app.schemas.auth_schema import Login, MenssageResponse, Registrar, TokenResponse
from app.services.auth_service import login_service, logout_service, registro_service

router = APIRouter(prefix="/v1/auth", tags=["Autenticacion"])


@router.post("/registro")
async def registro_router(data: Registrar) -> MenssageResponse:
    return registro_service(data)


@router.post("/login")
async def login_router(data: Login) -> TokenResponse:
    return login_service(data)


@router.post("/logout")
async def logout_router() -> MenssageResponse:
    return logout_service()
