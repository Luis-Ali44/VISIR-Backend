from pydantic import BaseModel


class ConsultaRequest(BaseModel):
    pregunta: str


class EmbeddingUsado(BaseModel):
    id: str
    texto: str


class ConsultaResponse(BaseModel):
    id_consulta: str
    respuesta: str
    Embeddings_usados: list[EmbeddingUsado]
    distancia: float | None


class SaveConsulta(BaseModel):
    id_consulta: str
    respuesta: str
    id_usuario: str
    id_organizacion: str
