from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CrearConversacionRequest(BaseModel):
    pregunta: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class ContinuarConversacionRequest(BaseModel):
    pregunta: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class FuenteCitadaConversacion(BaseModel):
    filename: str
    chunk_id: str
    section: str
    page_number: int | None = None
    similarity: float
    origen: Literal["ley", "cfdi"]


class TurnoResponse(BaseModel):
    id: str
    mensaje_usuario: str
    respuesta_sistema: str
    created_at: datetime


class SesionListaItem(BaseModel):
    sesion_id: str
    ultimo_mensaje: str | None = None
    created_at: datetime
    num_turnos: int


class SesionDetalleResponse(BaseModel):
    sesion_id: str
    contexto: dict[str, Any] | None = None
    turnos: list[TurnoResponse]


class SesionCreadaResponse(BaseModel):
    sesion_id: str
    respuesta: str
    ruta_ejecutada: str | None = None
    tiene_cobertura: bool
    confianza_score: float | None = None
    accion_seleccionada: Literal["responder", "responder_con_advertencia", "preguntar"] | None = (
        None
    )
    fuentes_citadas: list[FuenteCitadaConversacion] = Field(default_factory=list)
    latencias_ms: dict[str, float] = Field(default_factory=dict)


class SesionContinuadaResponse(BaseModel):
    sesion_id: str
    respuesta: str
    ruta_ejecutada: str | None = None
    tiene_cobertura: bool
    confianza_score: float | None = None
    accion_seleccionada: Literal["responder", "responder_con_advertencia", "preguntar"] | None = (
        None
    )
    fuentes_citadas: list[FuenteCitadaConversacion] = Field(default_factory=list)
    latencias_ms: dict[str, float] = Field(default_factory=dict)
