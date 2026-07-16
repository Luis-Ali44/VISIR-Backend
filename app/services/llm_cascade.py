"""
V-11.3 -- Router por complejidad de query para la cascada de LLMs.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

_ERRORES_FALLBACK = (
    "rate_limit",
    "ratelimit",
    "rate limit",
    "429",
    "timeout",
    "timed out",
    "503",
    "502",
    "overloaded",
    "service unavailable",
)


@dataclass
class TierConfig:
    nombre: str
    base_url: str
    api_key: str
    model: str
    max_tokens: int = 2048


@dataclass
class ResultadoCascada:
    texto_esquema: Any
    tier_solicitado: str
    tier_usado: str
    motivo_fallback: str | None
    latencia_ms: int
    tokens_entrada: int
    tokens_salida: int


def _es_error_de_fallback(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(marca in msg for marca in _ERRORES_FALLBACK)


def evaluar_complejidad(
    pregunta: str,
    ruta_seleccionada: str,
    n_fuentes_recuperadas: int,
) -> float:
    score = 0.0
    palabras = len(pregunta.split())
    score += min(palabras / 60, 0.4)

    if ruta_seleccionada == "HIBRIDO":
        score += 0.4
    elif ruta_seleccionada == "CFDI_PROPIOS":
        score += 0.15

    score += min(n_fuentes_recuperadas / 20, 0.2)

    return min(score, 1.0)


class LLMCascadeRouter:
    def __init__(
        self,
        tier_groq: TierConfig,
        tier_fallback: TierConfig | None,
        umbral_complejidad: float = 0.55,
        registrar_log: bool = True,
    ) -> None:
        self.tier_groq = tier_groq
        self.tier_fallback = tier_fallback
        self.umbral_complejidad = umbral_complejidad
        self.registrar_log = registrar_log

    def _cliente(self, tier: TierConfig, schema: Any, temperature: float) -> Any:
        return ChatOpenAI(
            model=tier.model,
            temperature=temperature,
            api_key=tier.api_key,
            base_url=tier.base_url,
            max_tokens=tier.max_tokens,
        ).with_structured_output(schema, include_raw=True)

    def invocar(
        self,
        mensajes: list,
        schema: Any,
        temperature: float,
        complejidad: float,
        id_organizacion: str | None = None,
    ) -> ResultadoCascada:
        tier_solicitado = "groq"
        tier_a_usar = self.tier_groq
        motivo_fallback: str | None = None

        if complejidad >= self.umbral_complejidad and self.tier_fallback is not None:
            tier_solicitado = "fallback"
            tier_a_usar = self.tier_fallback
            motivo_fallback = "complejidad_alta"

        inicio = time.monotonic()
        try:
            llm = self._cliente(tier_a_usar, schema, temperature)
            raw = llm.invoke(mensajes)
            tier_usado = tier_a_usar.nombre
        except Exception as exc:
            if self.tier_fallback is None or tier_a_usar.nombre == self.tier_fallback.nombre:
                logger.error("Fallo el ultimo tier disponible (%s): %s", tier_a_usar.nombre, exc)
                raise
            logger.warning(
                "Fallo tier %s, cayendo a fallback: %s",
                tier_a_usar.nombre,
                exc,
            )
            motivo_fallback = "rate_limit" if _es_error_de_fallback(exc) else "error_api"
            llm = self._cliente(self.tier_fallback, schema, temperature)
            raw = llm.invoke(mensajes)
            tier_usado = self.tier_fallback.nombre

        latencia_ms = int((time.monotonic() - inicio) * 1000)
        parsed = raw["parsed"]
        ai_msg = raw["raw"]
        usage = getattr(ai_msg, "usage_metadata", None) or {}
        tokens_entrada = usage.get("input_tokens", 0)
        tokens_salida = usage.get("output_tokens", 0)

        resultado = ResultadoCascada(
            texto_esquema=parsed,
            tier_solicitado=tier_solicitado,
            tier_usado=tier_usado,
            motivo_fallback=motivo_fallback,
            latencia_ms=latencia_ms,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
        )

        if self.registrar_log:
            self._log(resultado, complejidad, id_organizacion)

        return resultado

    def _log(
        self, resultado: ResultadoCascada, complejidad: float, id_organizacion: str | None
    ) -> None:
        try:
            from app.repositories.llm_router_log_repository import registrar_uso

            registrar_uso(
                id_organizacion=id_organizacion,
                tier_solicitado=resultado.tier_solicitado,
                tier_usado=resultado.tier_usado,
                motivo_fallback=resultado.motivo_fallback,
                complejidad_score=complejidad,
                tokens_entrada=resultado.tokens_entrada,
                tokens_salida=resultado.tokens_salida,
                latencia_ms=resultado.latencia_ms,
                exito=True,
            )
        except Exception as exc:
            logger.error("No se pudo registrar uso de la cascada de LLMs: %s", exc)


def cascada_desde_env() -> LLMCascadeRouter:
    import os

    tier_groq = TierConfig(
        nombre="groq",
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        api_key=os.getenv("LLM_API_KEY", ""),
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
    )

    fallback_api_key = os.getenv("LLM_FALLBACK_API_KEY", "")
    tier_fallback = None
    if fallback_api_key:
        tier_fallback = TierConfig(
            nombre="fallback",
            base_url=os.getenv("LLM_FALLBACK_BASE_URL", "https://api.openai.com/v1"),
            api_key=fallback_api_key,
            model=os.getenv("LLM_FALLBACK_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("LLM_FALLBACK_MAX_TOKENS", "2048")),
        )

    return LLMCascadeRouter(
        tier_groq=tier_groq,
        tier_fallback=tier_fallback,
        umbral_complejidad=float(os.getenv("LLM_CASCADE_UMBRAL_COMPLEJIDAD", "0.55")),
    )
