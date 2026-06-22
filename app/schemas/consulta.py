# app/schemas/consulta_v2.py
from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field

class ConsultaRequest(BaseModel):
    pregunta: str = Field(..., min_length=3, max_length=2000, description="Pregunta fiscal del usuario")
    top_k: int = Field(default=5, ge=1, le=20, description="Número de fragmentos a recuperar del RAG")

class DecisionEnrutamiento(BaseModel):
    ruta: Literal["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"] = Field(..., description="Ruta final determinada.")
    justificacion: str = Field(..., description="Razón técnica de la selección de ruta.")
    confianza: float = Field(..., description="Nivel de certeza del enrutamiento.")

class ConsultaResponse(BaseModel):
    solicitud_id: str
    respuesta: str
    tiene_cobertura: bool
    fuentes_citadas: list[str]
    latencias_ms: dict[str, float]

# --- ESTADO DE LA MÁQUINA DE ESTADOS (LANGGRAPH) ---
class VisirState(TypedDict):
    pregunta: str
    usuario_id: str
    id_organizacion: str
    top_k: int
    
    # Variables de Control de la Máquina de Estados del Enrutador
    ruta_seleccionada: Literal["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"] | None
    confianza_lexica: float
    palabras_clave_detectadas: list[str]
    decision_enrutamiento: DecisionEnrutamiento | None
    
    # Datos de los Nodos de Recuperación
    fragmentos_leyes: list[dict[str, Any]]
    datos_cfdi: dict[str, Any]
    estadisticas_cfdi: dict[str, Any]
    
    # Respuestas y Salida
    respuesta_final: str | None