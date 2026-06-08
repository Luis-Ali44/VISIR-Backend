from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_user, security
from app.schemas.auth_schema import Login, MenssageResponse, Registrar, TokenResponse
from app.schemas.user_schema import UsuarioActual
from app.services.auth_service import login_service, logout_service, registro_service

router = APIRouter(prefix="/v1/auth", tags=["Autenticacion"])


@router.post("/registro")
async def registro_router(data: Registrar) -> MenssageResponse:
    return registro_service(data)


@router.post("/login")
async def login_router(data: Login) -> TokenResponse:
    return login_service(data)


@router.post("/logout")
async def logout_router(
    user: UsuarioActual = Depends(get_user),
    credenciales: HTTPAuthorizationCredentials = Depends(security),
) -> MenssageResponse:
    jwt_token = credenciales.credentials
    return logout_service(jwt_token)
