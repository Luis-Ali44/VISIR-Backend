from pydantic import BaseModel, Field, field_validator

class ConsultaRequest(BaseModel):
    pregunta: str = Field(..., min_length=1, description="Pregunta fiscal del usuario")
    top_k: int = Field(5, ge=1, le=10, description="Número de fragmentos a recuperar")

    @field_validator("pregunta")
    @classmethod
    def pregunta_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La pregunta no puede contener solo espacios")
        return v.strip()


class ChunkInfo(BaseModel):
    chunk_id: str
    fuente: str
    seccion: str
    pagina: int | None = None
    similitud: float


class TokenUsage(BaseModel):
    tokens_entrada: int = Field(..., ge=0, description="Tokens consumidos por pregunta + contexto")
    tokens_salida: int  = Field(..., ge=0, description="Tokens consumidos por la respuesta del LLM")


class ConsultaResponse(BaseModel):
    solicitud_id: str
    respuesta: str
    tiene_cobertura: bool = Field(..., description="El contexto cubría la pregunta")
    fuentes_citadas: list[str] = Field(default_factory=list, description="Archivos citados por el LLM")
    chunks_recuperados: list[ChunkInfo]
    fuentes: list[str]
    latencias_ms: dict[str, float]
    tokens: TokenUsage


class EmbeddingRequest(BaseModel):
    texto: str = Field(..., min_length=1, max_length=8000, description="Texto a vectorizar")


class EmbeddingResponse(BaseModel):
    texto: str
    modelo: str
    dimensiones: int
    vector: list[float]


class BusquedaSemanticaRequest(BaseModel):
    texto: str = Field(..., min_length=1, description="Texto de consulta")
    top_k: int = Field(5, ge=1, le=20, description="Número de resultados")
    rerank: bool = Field(True, description="Aplicar reranking por importancia")


class BusquedaSemanticaResponse(BaseModel):
    texto_consulta: str
    resultados: list[ChunkInfo]
    total: int