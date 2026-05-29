from fastapi import APIRouter, status

from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from app.services.auth_service import login_service, logout_service, registrar_service

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


@router.post("/registrar", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def registro(data: RegisterRequest) -> MessageResponse:
    return registrar_service(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest) -> TokenResponse:
    return login_service(data)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout() -> dict[str, str]:
    return logout_service()
