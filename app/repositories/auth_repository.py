from typing import Any

from app.core.database import get_auth_client
from app.schemas.auth_schema import Login, Registrar


def registro_repository(data: Registrar) -> Any:
    
    auth_client = get_auth_client()
    response = auth_client.auth.sign_up(
        {
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "nombre": data.nombre,
                    "apellido_paterno": data.apellido_paterno,
                    "apellido_materno": data.apellido_materno,
                }
            },
        }
    )
    return response


def login_repository(data: Login) -> Any:
    
    auth_client = get_auth_client()
    response = auth_client.auth.sign_in_with_password(
        {"email": data.email, "password": data.password}
    )

    return response


def logout_repository(jwt_token: str) -> Any:
    auth_client = get_auth_client()
    auth_client.auth.set_session(jwt_token, "")
    auth_client.auth.sign_out()
    return True
