from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    nombre: str
    tipo: str
    tamaño: int | None = None
    link: str
    id_usuario: UUID | None = None
    id_organizacion: UUID | None = None
    id_categorias: UUID | None
    hash_archivo: str


class DocumentResponse(BaseModel):
    id: UUID
    nombre: str
    tipo: str
    tamaño: int | None = None
    link: str
    id_usuario: UUID | None = None
    id_organizacion: UUID | None = None
    id_categorias: UUID | None
    created_at: datetime


class DocumentoFallido(BaseModel):
    nombre_archivo: str
    error: str


class LoteResponse(BaseModel):
    exitosos: list[DocumentResponse]
    fallidos: list[DocumentoFallido]
