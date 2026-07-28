from typing import Any

from app.core.config import settings
from app.repositories.base_repository import BaseRepository
from app.schemas.auth_schema import Login, Registrar
from supabase import create_client


class AuthRepository(BaseRepository):
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLIC_KEY)

    def registro_repository(self, data: Registrar) -> Any:
        response = self.db.auth.sign_up(
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

    def login_repository(self, data: Login) -> Any:
        response = self.client.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )

        return response

    def logout_repository(self, jwt_token: str) -> None:
        try:
            self.db.auth.set_session(jwt_token, "")
            self.db.auth.sign_out()
        except Exception as e:
            print(f"Error al cerrar sesión: {e}")
