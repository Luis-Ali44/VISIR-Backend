"""
Agrega los resultados de los 3 evals (Recall, Routing, Confianza)
en un solo metrics_summary.json para el dashboard.

Uso (después de correr los 3 evals):
  uv run python -m evaluaciones.agregar_metricas
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))


def _buscar_ultimo_json(directorio: Path, patron: str) -> dict:
    archivos = sorted(directorio.glob(patron), key=lambda p: p.stat().st_mtime, reverse=True)
    if not archivos:
        return {}
    try:
        return json.loads(archivos[0].read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    output_dir = _ROOT / "validation_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    eval_recall = _buscar_ultimo_json(output_dir, "eval_recall_*.json")
    eval_ruteo = _buscar_ultimo_json(output_dir, "eval_ruteo_*.json")
    eval_conf_baseline = _buscar_ultimo_json(output_dir, "eval_confianza_baseline_*.json")
    eval_conf_modelo = _buscar_ultimo_json(output_dir, "eval_confianza_modelo_*.json")

    recall_global = eval_recall.get("recall_global", {})
    routing_data = eval_ruteo.get("enrutamiento", {})
    confianza_data = eval_conf_modelo.get("confianza", {}) or eval_conf_baseline.get(
        "confianza", {}
    )

    summary = {
        "timestamp": datetime.now().isoformat(),
        "commit": "",
        "recall_at_1": recall_global.get("recall_at_1", 0),
        "recall_at_3": recall_global.get("recall_at_3", 0),
        "recall_at_5": recall_global.get("recall_at_5", 0),
        "total_preguntas": recall_global.get("total_preguntas", 0),
        "routing_precision": routing_data.get("precision", 0),
        "routing_total": routing_data.get("total", 0),
        "confianza_precision_accion": confianza_data.get("precision_accion", 0),
        "confianza_precision_confianza": confianza_data.get("precision_confianza", 0),
        "confianza_total": confianza_data.get("total", 0),
        "confianza_detalle": confianza_data.get("detalle", []),
    }

    path = output_dir / "metrics_summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[METRICS] Resumen guardado en {path}")


if __name__ == "__main__":
    main()
