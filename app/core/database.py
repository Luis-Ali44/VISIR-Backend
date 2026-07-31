from dataclasses import dataclass
from typing import Literal

from supabase.client import Client, ClientOptions, create_client

from app.core.config import settings
from app.schemas.user_schema import UsuarioActual


@dataclass(frozen=True)
class ExecCtx:
    actor: Literal["user", "system"]
    id_organizacion: str
    id_usuario: str | None = None
    jwt: str | None = None

    @classmethod
    def from_user(cls, user: UsuarioActual, jwt: str | None = None) -> "ExecCtx":
        return cls(actor="user", id_organizacion=user.id_organizacion, id_usuario=user.id, jwt=jwt)


def cliente_for(ctx: ExecCtx) -> Client:
    if ctx.actor == "user":
        if not ctx.jwt:
            raise ValueError("Se requiere un jwt válido para el contexto de usuario")
        c = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_PUBLIC_KEY,
            options=ClientOptions(headers={"Authorization": f"Bearer {ctx.jwt}"}),
        )
        c.postgrest.auth(ctx.jwt)
        return c

    if not ctx.id_organizacion:
        raise ValueError("Contexto system sin organización")

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
