from fastapi import HTTPException, status

from app.repositories.auth_repository import (
    login_repository,
    logout_repository,
    registro_repository,
)
from app.schemas.auth_schema import Login, MenssageResponse, Registrar, TokenResponse


def registro_service(data: Registrar) -> MenssageResponse:
    try:
        pass_lower = data.password.lower()

        if (
            (pass_lower == data.email.lower())
            or (pass_lower == data.nombre.lower())
            or (pass_lower == data.apellido_paterno.lower())
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tu contraseña no puede ser igual correo, nombre o apellido",
            )

        response = registro_repository(data)

        if not response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error al crear usuario"
            )

        return MenssageResponse(menssage="Usuario creado. Revise su correo para confirmar")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error interno: {e!r}"
        ) from e


def login_service(data: Login) -> TokenResponse:
    try:
        response = login_repository(data)

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrecta"
            )
        return TokenResponse(token=response.session.access_token, token_type="Bearer")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos"
        ) from e


def logout_service(jwt_token: str) -> MenssageResponse:
    logout_repository(jwt_token)
    return MenssageResponse(menssage="Sesion Cerrada")
