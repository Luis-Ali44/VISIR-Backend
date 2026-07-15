import json
import logging
import os
import pickle
from pathlib import Path

import mlflow
import numpy as np

from app.services.confidence_config import (
    BASELINE_PESOS,
    FEATURES,
    UMBRAL_ADVERTENCIA,
    UMBRAL_RESPONDER,
)

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    def __init__(self, model_path: str | None = None):
        self.model = None
        self.model_path = model_path or ""
        self.umbral_responder = UMBRAL_RESPONDER
        self.umbral_advertencia = UMBRAL_ADVERTENCIA

        report_path = self._report_path()
        if report_path and report_path.exists():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
                ua = report.get("umbrales_accion")
                if ua:
                    self.umbral_responder = float(ua.get("responder_desde", self.umbral_responder))
                    raw_adv = ua.get("advertencia_desde", self.umbral_advertencia)
                    self.umbral_advertencia = float(raw_adv)
                    logger.info(
                        "Umbrales cargados desde reporte: responder≥%.4f advertencia≥%.4f",
                        self.umbral_responder,
                        self.umbral_advertencia,
                    )
            except Exception as exc:
                logger.warning("No se pudieron cargar umbrales del reporte: %s", exc)

        self.model = self._cargar_modelo_mlflow()
        if self.model is None and self.model_path and Path(self.model_path).exists():
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("Modelo de confianza cargado: %s", self.model_path)
            except Exception as exc:
                logger.error(
                    "Error al cargar modelo desde '%s': %s — usando baseline de pesos fijos",
                    self.model_path,
                    exc,
                )
                self.model = None
        elif self.model is None:
            logger.warning(
                "Modelo no encontrado en '%s' — usando baseline de pesos fijos",
                self.model_path or "(no configurado)",
            )

    def _cargar_modelo_mlflow(self):
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        if not tracking_uri:
            return None
        try:
            mlflow.set_tracking_uri(tracking_uri)
            modelo = mlflow.pyfunc.load_model("models:/confianza_ridge@produccion")
            logger.info("Modelo confianza_ridge cargado desde MLflow (alias produccion)")
            return modelo
        except Exception as exc:
            logger.warning(
                "No se pudo cargar el modelo desde MLflow (%s), cayendo a archivo local (%s)",
                exc,
                self.model_path,
            )
            return None

    def _report_path(self) -> Path | None:
        if not self.model_path:
            return None
        mp = Path(self.model_path)
        return mp.parent / "reporte_entrenamiento.json" if mp.parent else None

    def _preparar_X(self, features: dict[str, float]):  # noqa: N802
        X = np.array([[features.get(col, 0.0) for col in FEATURES]], dtype=float)  # noqa: N806
        if hasattr(self.model, "_model_meta"):
            try:
                import pandas as pd  # type: ignore[import-untyped]

                X = pd.DataFrame(X, columns=FEATURES)  # noqa: N806
            except ImportError:
                pass
        return X

    def calcular(self, features: dict[str, float]) -> float:
        if self.model is not None:
            try:
                X = self._preparar_X(features)  # noqa: N806
                return float(np.clip(self.model.predict(X)[0], 0.0, 1.0))
            except Exception as exc:
                logger.error(
                    "Error en model.predict con features=%s: %s — cayendo a baseline",
                    features,
                    exc,
                )
        score = 0.0
        for col, peso in BASELINE_PESOS.items():
            score += features.get(col, 0.0) * peso
        return min(max(score, 0.0), 1.0)

    def decidir_accion(self, score: float) -> str:
        if score >= self.umbral_responder:
            return "responder"
        if score >= self.umbral_advertencia:
            return "responder_con_advertencia"
        return "preguntar"

    @property
    def version(self) -> str:
        if self.model is not None:
            if hasattr(self.model, "_model_meta"):
                return "mlflow(confianza_ridge@produccion)"
            return f"ridge({self.model_path})"
        return "baseline_pesos_fijos"
