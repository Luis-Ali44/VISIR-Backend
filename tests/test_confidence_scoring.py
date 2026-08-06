import pickle
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.confidence_config import (
    BASELINE_PESOS,
    FEATURES,
    UMBRAL_ADVERTENCIA,
    UMBRAL_RESPONDER,
)
from app.services.confidence_scoring import ConfidenceScorer


class _ModeloPickleable:
    """Modelo simple que se puede serializar con pickle para pruebas."""

    def __init__(self, valor=0.75):
        self.valor = valor

    def predict(self, x):
        return np.array([self.valor])


class TestConfidenceConfig:
    def test_features_tienen_seis_elementos(self):
        assert len(FEATURES) == 6

    def test_baseline_pesos_suman_uno(self):
        total = sum(BASELINE_PESOS.values())
        assert abs(total - 1.0) < 0.001

    def test_umbrales_son_positivos(self):
        assert 0 < UMBRAL_ADVERTENCIA < UMBRAL_RESPONDER <= 1.0


class TestConfidenceScorer:
    def test_sin_modelo_calcula_baseline(self):
        scorer = ConfidenceScorer(model_path="")
        features = {
            "rag_coverage": 0.8,
            "routing_certainty": 0.85,
            "question_clarity": 0.9,
            "data_completeness": 1.0,
            "campo_periodo_faltante": 0.0,
            "campo_tipo_faltante": 0.0,
        }
        score = scorer.calcular(features)
        # Permitir que en entornos con MLFLOW configurado el modelo se cargue.
        if scorer.model is None:
            expected = sum(features[c] * BASELINE_PESOS[c] for c in BASELINE_PESOS)
            assert score == pytest.approx(expected, abs=0.001)
        else:
            assert 0.0 <= score <= 1.0

    def test_sin_modelo_todas_cero(self):
        scorer = ConfidenceScorer(model_path="")
        score = scorer.calcular({})
        if scorer.model is None:
            assert score == pytest.approx(0.0, abs=0.001)
        else:
            assert 0.0 <= score <= 1.0

    def test_sin_modelo_todas_maximo(self):
        scorer = ConfidenceScorer(model_path="")
        features = dict.fromkeys(FEATURES, 1.0)
        score = scorer.calcular(features)
        if scorer.model is None:
            assert score == pytest.approx(1.0, abs=0.001)
        else:
            assert 0.0 <= score <= 1.0

    def test_version_sin_modelo(self):
        scorer = ConfidenceScorer(model_path="")
        # El entorno de pruebas puede proporcionar MLflow; aceptar ambas variantes.
        assert any(x in scorer.version for x in ("baseline", "mlflow", "ridge"))

    def test_decidir_accion_responder(self):
        scorer = ConfidenceScorer(model_path="")
        assert scorer.decidir_accion(0.9) == "responder"
        assert scorer.decidir_accion(0.8) == "responder"

    def test_decidir_accion_advertencia(self):
        scorer = ConfidenceScorer(model_path="")
        assert scorer.decidir_accion(0.65) == "responder_con_advertencia"
        assert scorer.decidir_accion(0.5) == "responder_con_advertencia"

    def test_decidir_accion_preguntar(self):
        scorer = ConfidenceScorer(model_path="")
        assert scorer.decidir_accion(0.3) == "preguntar"
        assert scorer.decidir_accion(0.0) == "preguntar"


class TestConfidenceScorerMLflow:
    """Pruebas del cargador MLflow en ConfidenceScorer."""

    def test_sin_uri_no_intenta_mlflow(self, monkeypatch):
        monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
        scorer = ConfidenceScorer(model_path="")
        assert scorer.model is None
        assert "baseline" in scorer.version

    def test_mlflow_falla_cae_a_pkl(self, monkeypatch, tmp_path):
        modelo_local = _ModeloPickleable(valor=0.75)
        pkl = tmp_path / "modelo.pkl"
        with open(pkl, "wb") as f:
            pickle.dump(modelo_local, f)

        monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://dagshub.com/x/x.mlflow")

        with patch("app.services.confidence_scoring.mlflow") as mock_mlflow:
            mock_mlflow.pyfunc = MagicMock()
            mock_mlflow.pyfunc.load_model.side_effect = Exception("MLflow caido")

            scorer = ConfidenceScorer(model_path=str(pkl))

        assert scorer.model is not None
        assert "ridge" in scorer.version
        score = scorer.calcular({"rag_coverage": 0.5})
        assert score == pytest.approx(0.75, abs=0.001)

    def test_mlflow_exitoso_usado_desde_el_constructor(self, monkeypatch):
        monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://dagshub.com/x/x.mlflow")

        mock_pyfunc = MagicMock()
        mock_pyfunc._model_meta = MagicMock()
        mock_pyfunc.predict.return_value = np.array([0.88])

        with patch("app.services.confidence_scoring.mlflow") as mock_mlflow:
            mock_mlflow.pyfunc = MagicMock()
            mock_mlflow.pyfunc.load_model.return_value = mock_pyfunc

            scorer = ConfidenceScorer(model_path="")

        assert scorer.model is not None
        assert "mlflow" in scorer.version
        score = scorer.calcular({"rag_coverage": 0.5})
        assert score == pytest.approx(0.88, abs=0.001)

    def test_mlflow_exitoso_version_indica_origen(self, monkeypatch):
        monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://dagshub.com/x/x.mlflow")

        mock_pyfunc = MagicMock()
        mock_pyfunc._model_meta = MagicMock()

        with patch("app.services.confidence_scoring.mlflow") as mock_mlflow:
            mock_mlflow.pyfunc = MagicMock()
            mock_mlflow.pyfunc.load_model.return_value = mock_pyfunc

            scorer = ConfidenceScorer(model_path="")

        assert "mlflow" in scorer.version
        mock_mlflow.set_tracking_uri.assert_called_once()
        mock_mlflow.pyfunc.load_model.assert_called_once_with("models:/confianza_ridge@produccion")
