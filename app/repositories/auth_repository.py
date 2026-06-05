from typing import Any

from app.core.database import supabase
from app.schemas.auth_schema import Login, Registrar


def registro_repository(data: Registrar) -> Any:
    supabase.auth.sign_up(
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


def login_repository(data: Login) -> Any:
    response = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})

    return response


def logout_repository() -> Any:
    supabase.auth.sign_out()
