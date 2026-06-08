from pydantic import BaseModel


class UsuarioActual(BaseModel):
    id: str
    id_organizacion: str | None
