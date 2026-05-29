from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    nombre: str
    tipo: str
    tamaño: int | None = None
    id_usuario: UUID
    id_organizacion: UUID


class DocumentResponse(BaseModel):
    id: UUID
    nombre: str
    tipo: str
    tamaño: int | None = None
    link: str
    id_usuario: UUID | None = None
    id_organizacion: UUID | None = None
    created_at: datetime
