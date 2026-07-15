from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class ConsultaRequest(BaseModel):
    pregunta: str = Field(
        ..., min_length=3, max_length=2000, description="Pregunta fiscal del usuario"
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Número de fragmentos a recuperar del RAG"
    )


class DecisionEnrutamiento(BaseModel):
    ruta: Literal["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"] = Field(
        ..., description="Ruta final determinada."
    )
    justificacion: str = Field(..., description="Razón técnica de la selección de ruta.")
    confianza: float = Field(..., description="Nivel de certeza del enrutamiento.")


class FuenteCitada(BaseModel):
    filename: str = Field(..., description="Archivo o documento fuente del fragmento.")
    chunk_id: str = Field(..., description="ID único del chunk en ChromaDB.")
    section: str = Field(..., description="Sección o encabezado del fragmento.")
    page_number: int | None = Field(None, description="Número de página en el documento original.")
    similarity: float = Field(..., description="Score de similitud coseno [0, 1].")
    origen: Literal["ley", "cfdi"] = Field(
        ...,
        description="'ley' si viene de FiscalRAGRetriever (normativa SAT), 'cfdi' si viene de OrgRAGRetriever.",
    )


class ConsultaResponse(BaseModel):
    solicitud_id: str
    respuesta: str
    tiene_cobertura: bool = Field(
        ...,
        description=(
            "True si al menos un fragmento recuperado supera el umbral de similitud configurado "
            "(RAG_COVERAGE_THRESHOLD). False indica respuesta de baja confianza."
        ),
    )
    confianza_score: float | None = Field(
        None,
        description="Puntaje de confianza del modelo V-10 [0,1]. None si no se ejecutó el scoring.",
    )
    accion_seleccionada: Literal["responder", "responder_con_advertencia", "preguntar"] | None = (
        Field(
            None,
            description="Acción determinada por el scorer de confianza basada en confianza_score.",
        )
    )
    fuentes_citadas: list[FuenteCitada] = Field(
        default_factory=list,
        description="Fragmentos reales del RAG que respaldan la respuesta, ordenados por similitud desc.",
    )
    latencias_ms: dict[str, float]


class VisirState(TypedDict):
    pregunta: str
    usuario_id: str
    id_organizacion: str
    top_k: int

    ruta_seleccionada: Literal["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"] | None
    confianza_lexica: float
    palabras_clave_detectadas: list[str]
    decision_enrutamiento: DecisionEnrutamiento | None

    fragmentos_leyes: list[dict[str, Any]]
    datos_cfdi: dict[str, Any]
    estadisticas_cfdi: dict[str, Any]

    respuesta_final: str | None
    fuentes_recuperadas: list[dict[str, Any]]

    confianza_score: float
    accion_seleccionada: Literal["responder", "responder_con_advertencia", "preguntar"] | None

    tokens_entrada: int
    tokens_salida: int
    tiene_cobertura: bool

    historial: list[dict[str, str]]
