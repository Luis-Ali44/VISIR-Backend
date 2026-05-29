from typing import Any

from app.core.database import supabase
from app.schemas.auth import RegisterRequest


def create_auth_user(email: str, password: str, data: RegisterRequest) -> Any:
    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
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


def login_user(email: str, password: str) -> Any:
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return response


def logout_user() -> None:
    supabase.auth.sign_out()
