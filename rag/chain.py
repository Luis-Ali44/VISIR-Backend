from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

from rag.retriever import RetrievalContext


class ConsultaInput(BaseModel):

    pregunta: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Pregunta fiscal del usuario",
    )

    @field_validator("pregunta")
    @classmethod
    def no_solo_espacios(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("La pregunta no puede contener solo espacios en blanco.")
        return stripped


class RespuestaLLM(BaseModel):

    respuesta: str = Field(
        ...,
        description=(
            "Respuesta fiscal clara y precisa basada exclusivamente en el contexto. "
            "Si el contexto no cubre la pregunta, responder exactamente: "
            "'El contexto disponible no cubre esta pregunta.'"
        ),
    )
    tiene_cobertura: bool = Field(
        ...,
        description=(
            "True si el contexto contiene información suficiente para responder. "
            "False si la respuesta es 'El contexto disponible no cubre esta pregunta.'"
        ),
    )
    fuentes_citadas: list[str] = Field(
        default_factory=list,
        description="Lista de nombres de archivo citados en la respuesta (ej: 'RMF_2025.pdf').",
    )



class ChainResult(BaseModel):

    texto: str = Field(..., min_length=1, description="Respuesta generada por el LLM.")
    tiene_cobertura: bool = Field(..., description="El contexto cubría la pregunta.")
    fuentes_citadas: list[str] = Field(default_factory=list)
    tokens_entrada: int = Field(..., ge=0, description="Tokens consumidos por el prompt.")
    tokens_salida: int = Field(..., ge=0, description="Tokens consumidos por la respuesta.")


SYSTEM_PROMPT = """\
Eres un asistente fiscal especializado en la normativa del SAT de México.
Tu función es responder preguntas sobre CFDIs, regímenes fiscales, \
complementos y obligaciones tributarias de PyMEs.

Reglas estrictas:
1. Responde ÚNICAMENTE con información presente en el contexto proporcionado.
2. Si el contexto no contiene la respuesta, indica tiene_cobertura=false y \
responde: "El contexto disponible no cubre esta pregunta."
3. Cita el nombre de archivo fuente en fuentes_citadas cuando sea relevante.
4. Usa lenguaje claro y directo, sin jerga innecesaria.
5. Responde siempre en el idioma de la pregunta.
"""

HUMAN_PROMPT = """\
Contexto fiscal recuperado:
{contexto}

────────────────────────────────────────
Pregunta del usuario: {pregunta}
────────────────────────────────────────
Proporciona una respuesta clara y precisa basada exclusivamente en \
el contexto anterior.
"""


def format_context(fragmentos: list[RetrievalContext]) -> str:
    """Serializa los fragmentos recuperados en texto estructurado para el LLM."""
    if not fragmentos:
        return "No se encontraron fragmentos relevantes."

    parts: list[str] = []
    for i, ctx in enumerate(fragmentos, 1):
        page_info = f"p.{ctx.page_number}" if ctx.page_number else "N/A"
        header = (
            f"[FRAGMENTO {i} | {ctx.filename} | "
            f"Sección: {ctx.section[:60]} | "
            f"Página: {page_info} | "
            f"Relevancia: {ctx.similarity:.2f} | "
            f"chunk_id: {ctx.chunk_id}]"
        )
        parts.append(f"{header}\n{ctx.text}")

    return "\n\n---\n\n".join(parts)


class FiscalRAGChain:

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.groq.com/openai/v1",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> None:
        llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Nivel 2: fuerza al LLM a responder con el esquema RespuestaLLM
        self._llm = llm.with_structured_output(RespuestaLLM, include_raw=True)
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ])

    def invoke(self, pregunta: str, fragmentos: list[RetrievalContext]) -> ChainResult:
        # Nivel 1: valida la entrada del usuario
        entrada = ConsultaInput(pregunta=pregunta)

        messages = self._prompt.format_messages(
            pregunta=entrada.pregunta,
            contexto=format_context(fragmentos),
        )

        raw_result = self._llm.invoke(messages)

        respuesta_llm: RespuestaLLM = raw_result["parsed"]
        ai_message = raw_result["raw"]

        usage = getattr(ai_message, "usage_metadata", None) or {}
        tokens_entrada = usage.get("input_tokens", 0)
        tokens_salida = usage.get("output_tokens", 0)

        return ChainResult(
            texto=respuesta_llm.respuesta,
            tiene_cobertura=respuesta_llm.tiene_cobertura,
            fuentes_citadas=respuesta_llm.fuentes_citadas,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
        )