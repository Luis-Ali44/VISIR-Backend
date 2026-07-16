from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_cascade import (
    LLMCascadeRouter,
    TierConfig,
    _es_error_de_fallback,
    evaluar_complejidad,
)


def _tier(nombre: str) -> TierConfig:
    return TierConfig(nombre=nombre, base_url="http://x", api_key="k", model="m")


def _mock_raw(input_tokens: int = 10, output_tokens: int = 5) -> dict:
    ai_msg = MagicMock()
    ai_msg.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return {"parsed": {"respuesta": "ok"}, "raw": ai_msg}


class TestEvaluarComplejidad:
    def test_pregunta_corta_ruta_simple_es_baja_complejidad(self) -> None:
        score = evaluar_complejidad(
            "¿cuánto pagué de IVA?", "CFDI_PROPIOS", n_fuentes_recuperadas=2
        )
        assert score < 0.55

    def test_ruta_hibrida_sube_la_complejidad(self) -> None:
        score_simple = evaluar_complejidad("pregunta corta", "NORMATIVA", n_fuentes_recuperadas=2)
        score_hibrido = evaluar_complejidad("pregunta corta", "HIBRIDO", n_fuentes_recuperadas=2)
        assert score_hibrido > score_simple

    def test_complejidad_nunca_pasa_de_uno(self) -> None:
        score = evaluar_complejidad(
            " ".join(["palabra"] * 200), "HIBRIDO", n_fuentes_recuperadas=50
        )
        assert score <= 1.0


class TestEsErrorDeFallback:
    @pytest.mark.parametrize(
        "mensaje", ["Rate limit exceeded", "Request timed out", "503 Service Unavailable"]
    )
    def test_detecta_errores_de_infraestructura(self, mensaje: str) -> None:
        assert _es_error_de_fallback(Exception(mensaje)) is True

    def test_no_marca_errores_genericos_como_fallback(self) -> None:
        assert _es_error_de_fallback(Exception("invalid schema field")) is False


class TestLLMCascadeRouter:
    def test_usa_groq_cuando_complejidad_es_baja(self) -> None:
        router = LLMCascadeRouter(
            _tier("groq"), _tier("fallback"), umbral_complejidad=0.55, registrar_log=False
        )
        with patch.object(router, "_cliente") as mock_cliente:
            mock_cliente.return_value.invoke.return_value = _mock_raw()
            resultado = router.invocar([], schema=dict, temperature=0.2, complejidad=0.1)
        assert resultado.tier_solicitado == "groq"
        assert resultado.tier_usado == "groq"
        assert resultado.motivo_fallback is None

    def test_usa_fallback_cuando_complejidad_es_alta(self) -> None:
        router = LLMCascadeRouter(
            _tier("groq"), _tier("fallback"), umbral_complejidad=0.55, registrar_log=False
        )
        with patch.object(router, "_cliente") as mock_cliente:
            mock_cliente.return_value.invoke.return_value = _mock_raw()
            resultado = router.invocar([], schema=dict, temperature=0.2, complejidad=0.9)
        assert resultado.tier_solicitado == "fallback"
        assert resultado.tier_usado == "fallback"
        assert resultado.motivo_fallback == "complejidad_alta"

    def test_cae_a_fallback_si_groq_falla(self) -> None:
        router = LLMCascadeRouter(
            _tier("groq"), _tier("fallback"), umbral_complejidad=0.55, registrar_log=False
        )
        llm_groq = MagicMock()
        llm_groq.invoke.side_effect = Exception("429 rate limit")
        llm_fallback = MagicMock()
        llm_fallback.invoke.return_value = _mock_raw()

        with patch.object(router, "_cliente", side_effect=[llm_groq, llm_fallback]):
            resultado = router.invocar([], schema=dict, temperature=0.2, complejidad=0.1)

        assert resultado.tier_solicitado == "groq"
        assert resultado.tier_usado == "fallback"
        assert resultado.motivo_fallback == "rate_limit"

    def test_sin_tier_fallback_relanza_el_error(self) -> None:
        router = LLMCascadeRouter(_tier("groq"), tier_fallback=None, registrar_log=False)
        with patch.object(router, "_cliente") as mock_cliente:
            mock_cliente.return_value.invoke.side_effect = Exception("boom")
            with pytest.raises(Exception, match="boom"):
                router.invocar([], schema=dict, temperature=0.2, complejidad=0.1)
