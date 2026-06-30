from typing import Any

from app.core.database import get_auth_client
from app.schemas.auth_schema import Login, Registrar


def registro_repository(data: Registrar) -> Any:
    # Cliente efímero: sign_up() dispara un evento SIGNED_IN en supabase-py
    # que reemplazaría el header Authorization del cliente administrativo
    # compartido si se usara ese cliente aquí. Ver app/core/database.py.
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
            # Para redireccionar despues de registrarse
            #  'options': {
            #   'email_redirect_to': 'https://example.com/login',
            # },"""
        }
    )
    return response


def login_repository(data: Login) -> Any:
    # Mismo motivo que registro_repository: cliente nuevo y descartable.
    auth_client = get_auth_client()
    response = auth_client.auth.sign_in_with_password(
        {"email": data.email, "password": data.password}
    )

    return response


def logout_repository(jwt_token: str) -> Any:
    # set_session()/sign_out() también disparan eventos de auth
    # (SIGNED_OUT) — mismo motivo, cliente efímero y no el compartido.
    auth_client = get_auth_client()
    auth_client.auth.set_session(jwt_token, "")
    auth_client.auth.sign_out()
    return True
