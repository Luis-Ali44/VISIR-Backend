"""
juez.py
────────
Cadenas LangChain para evaluación del sistema RAG como "modelo como juez".

Dos cadenas independientes:
  ┌─────────────────────────────────────────────────────────────────┐
  │  FidelidadChain                                                 │
  │  {pregunta, fragmentos, respuesta_generada}                     │
  │       → PromptTemplate → ChatOpenAI (temp=0) → JsonOutputParser │
  │       → {"score": int, "afirmaciones_soportadas": [...], ...}   │
  ├─────────────────────────────────────────────────────────────────┤
  │  RelevanciaChain                                                │
  │  {pregunta, respuesta_generada, respuesta_esperada}             │
  │       → PromptTemplate → ChatOpenAI (temp=0) → JsonOutputParser │
  │       → {"score": int, "aspectos_respondidos": [...], ...}      │
  └─────────────────────────────────────────────────────────────────┘

Usa ChatOpenAI con base_url configurable (compatible con Groq, Ollama, etc.)
temperature=0.0 garantiza máximo determinismo para evaluaciones reproducibles.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI  # ← usa ChatOpenAI en lugar de ChatGroq

# ─────────────────────────────────────────────────────────────────────────────
# Carga de prompts desde archivos
# ─────────────────────────────────────────────────────────────────────────────

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {path}")
    return path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Parser robusto (limpia markdown code fences si el LLM las añade)
# ─────────────────────────────────────────────────────────────────────────────

class RobustJsonOutputParser(JsonOutputParser):
    """
    Extiende JsonOutputParser para manejar respuestas que incluyen
    bloques ```json ... ``` a pesar de las instrucciones del prompt.
    """

    def parse(self, text: str) -> dict:
        clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formateo de contexto
# ─────────────────────────────────────────────────────────────────────────────

def _format_fragmentos_para_juez(fragmentos: list[str | dict]) -> str:
    parts: list[str] = []
    for i, frag in enumerate(fragmentos, 1):
        if isinstance(frag, str):
            parts.append(f"[FRAGMENTO {i}]\n{frag}")
        elif isinstance(frag, dict):
            chunk_id = frag.get("chunk_id", "N/A")
            fuente = frag.get("fuente", frag.get("filename", "N/A"))
            texto = frag.get("texto", frag.get("text", ""))
            parts.append(f"[FRAGMENTO {i} | chunk_id: {chunk_id} | fuente: {fuente}]\n{texto}")
    return "\n\n---\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# FidelidadChain
# ─────────────────────────────────────────────────────────────────────────────

class FidelidadChain:
    """
    Evalúa si la respuesta generada está soportada por los fragmentos recuperados.
    Detecta alucinaciones: información que el LLM inventó más allá del contexto.

    Retorna:
        {
          "score": int (1-5),
          "afirmaciones_soportadas": list[str],
          "afirmaciones_sin_soporte": list[str],
          "razonamiento": str
        }
    """

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=0.0,
            max_tokens=600,
        )
        prompt = PromptTemplate(
            template=_load_prompt("fidelidad.txt"),
            input_variables=["pregunta", "fragmentos", "respuesta_generada"],
        )
        self._chain = prompt | llm | RobustJsonOutputParser()

    def evaluar(
        self,
        pregunta: str,
        fragmentos: list[str | dict],
        respuesta_generada: str,
    ) -> dict:
        return self._chain.invoke({
            "pregunta": pregunta,
            "fragmentos": _format_fragmentos_para_juez(fragmentos),
            "respuesta_generada": respuesta_generada,
        })


# ─────────────────────────────────────────────────────────────────────────────
# RelevanciaChain
# ─────────────────────────────────────────────────────────────────────────────

class RelevanciaChain:
    """
    Evalúa si la respuesta generada responde realmente la pregunta del usuario.

    Retorna:
        {
          "score": int (1-5),
          "aspectos_respondidos": list[str],
          "aspectos_faltantes": list[str],
          "razonamiento": str
        }
    """

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=0.0,
            max_tokens=600,
        )
        prompt = PromptTemplate(
            template=_load_prompt("relevancia.txt"),
            input_variables=["pregunta", "respuesta_generada", "respuesta_esperada"],
        )
        self._chain = prompt | llm | RobustJsonOutputParser()

    def evaluar(
        self,
        pregunta: str,
        respuesta_generada: str,
        respuesta_esperada: str,
    ) -> dict:
        return self._chain.invoke({
            "pregunta": pregunta,
            "respuesta_generada": respuesta_generada,
            "respuesta_esperada": respuesta_esperada,
        })


# ─────────────────────────────────────────────────────────────────────────────
# JuezFiscal — wrapper que agrupa ambas cadenas
# ─────────────────────────────────────────────────────────────────────────────

class JuezFiscal:
    """
    Wrapper que agrupa FidelidadChain y RelevanciaChain.

    Uso típico:
        juez = JuezFiscal(api_key="...", model="llama-3.3-70b-versatile",
                          base_url="https://api.groq.com/openai/v1")
        resultado = juez.evaluar_completo(...)
    """

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.fidelidad = FidelidadChain(api_key=api_key, model=model, base_url=base_url)
        self.relevancia = RelevanciaChain(api_key=api_key, model=model, base_url=base_url)

    def evaluar_completo(
        self,
        pregunta: str,
        fragmentos: list[str | dict],
        respuesta_generada: str,
        respuesta_esperada: str,
    ) -> dict:
        fid = self.fidelidad.evaluar(pregunta, fragmentos, respuesta_generada)
        rel = self.relevancia.evaluar(pregunta, respuesta_generada, respuesta_esperada)
        return {"fidelidad": fid, "relevancia": rel}
