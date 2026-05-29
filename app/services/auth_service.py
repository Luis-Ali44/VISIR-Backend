from fastapi import HTTPException, status

from app.repositories.auth_repository import create_auth_user, login_user, logout_user
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse


def registrar_service(data: RegisterRequest) -> MessageResponse:
    try:
        response = create_auth_user(data.email, data.password, data)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error al crear usuario"
            )

        return MessageResponse(message="Usuario creado. Revisa tu correo para confirmar.")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


def login_service(data: LoginRequest) -> TokenResponse:
    try:
        response = login_user(data.email, data.password)

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas"
            )

        return TokenResponse(access_token=response.session.access_token, token_type="bearer")

    except HTTPException:
        raise


def logout_service() -> dict[str, str]:
    logout_user()
    return {"message": "Sesion Cerrada"}
