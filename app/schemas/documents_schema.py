from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    nombre: str
    tipo: str
    tamano: int
