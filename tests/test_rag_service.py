from app.schemas.consulta import VisirState
from app.services.confidence_config import FEATURES


def make_state(overrides=None) -> VisirState:
    base: VisirState = {
        "pregunta": "¿Cuánto gasto en facturas este mes?",
        "usuario_id": "u1",
        "id_organizacion": "org1",
        "top_k": 5,
        "ruta_seleccionada": "NORMATIVA",
        "confianza_lexica": 0.9,
        "palabras_clave_detectadas": ["gasto", "factura"],
        "decision_enrutamiento": None,
        "fragmentos_leyes": [],
        "datos_cfdi": {},
        "estadisticas_cfdi": {},
        "respuesta_final": None,
        "fuentes_recuperadas": [],
        "confianza_score": 0.0,
        "accion_seleccionada": None,
        "tokens_entrada": 0,
        "tokens_salida": 0,
        "tiene_cobertura": False,
        "historial": [],
    }
    if overrides:
        base.update(overrides)
    return base


class TestRAGServiceStructure:
    def test_initial_state_has_required_fields(self):
        state = make_state()
        assert state["pregunta"] == "¿Cuánto gasto en facturas este mes?"
        assert state["tokens_entrada"] == 0
        assert state["tokens_salida"] == 0
        assert state["tiene_cobertura"] is False
        assert state["confianza_score"] == 0.0
        assert state["accion_seleccionada"] is None

    def test_initial_state_all_keys_present(self):
        state = make_state()
        required = {
            "pregunta",
            "usuario_id",
            "id_organizacion",
            "top_k",
            "ruta_seleccionada",
            "confianza_lexica",
            "palabras_clave_detectadas",
            "decision_enrutamiento",
            "fragmentos_leyes",
            "datos_cfdi",
            "estadisticas_cfdi",
            "respuesta_final",
            "fuentes_recuperadas",
            "confianza_score",
            "accion_seleccionada",
            "tokens_entrada",
            "tokens_salida",
            "tiene_cobertura",
            "historial",
        }
        assert set(state.keys()) == required

    def test_confidence_features_match_consume(self):
        assert "rag_coverage" in FEATURES
        assert "routing_certainty" in FEATURES
        assert "question_clarity" in FEATURES
        assert "data_completeness" in FEATURES
        assert "campo_periodo_faltante" in FEATURES
        assert "campo_tipo_faltante" in FEATURES
        assert len(FEATURES) == 6


class TestDestinoDesdeAccion:
    def _destino_desde_accion(self, accion, ruta):
        if accion == "preguntar":
            return "preparar_pregunta"
        if ruta == "HIBRIDO":
            return "sintesis_hibrida"
        if ruta == "CFDI_PROPIOS":
            return "responder_cfdis"
        return "responder_normativa"

    def test_preguntar_siempre_a_preparar(self):
        for r in ["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"]:
            assert self._destino_desde_accion("preguntar", r) == "preparar_pregunta"

    def test_responder_normativa(self):
        assert self._destino_desde_accion("responder", "NORMATIVA") == "responder_normativa"

    def test_responder_cfdis(self):
        assert self._destino_desde_accion("responder", "CFDI_PROPIOS") == "responder_cfdis"

    def test_responder_hibrido(self):
        assert self._destino_desde_accion("responder", "HIBRIDO") == "sintesis_hibrida"

    def test_advertencia_comportarse_igual_que_responder(self):
        for r in ["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"]:
            d1 = self._destino_desde_accion("responder", r)
            d2 = self._destino_desde_accion("responder_con_advertencia", r)
            assert d1 == d2
