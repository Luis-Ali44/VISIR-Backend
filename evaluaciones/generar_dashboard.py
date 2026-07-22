"""
Genera un dashboard HTML autocontenido a partir de los resultados
de evaluación más recientes en validation_results/.

Uso:
  uv run python -m evaluaciones.generar_dashboard
  uv run python -m evaluaciones.generar_dashboard --output-dir validation_results

Busca archivos validation_results/eval_*.json y validation_results/metrics_summary.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard — Evaluación VISIR</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f7fa; color: #1a1a2e; padding: 2rem; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  .subtitle {{ color: #666; margin-bottom: 2rem; }}
  .grid {{ display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem; margin-bottom: 2rem; }}
  .card {{ background: white; border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .card h2 {{ font-size: 1rem; color: #666; margin-bottom: 0.5rem; }}
  .card .value {{ font-size: 2.2rem; font-weight: 700; }}
  .card .value.pass {{ color: #22c55e; }}
  .card .value.fail {{ color: #ef4444; }}
  .card .value.warn {{ color: #f59e0b; }}
  canvas {{ max-height: 300px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #eee;
    font-size: 0.9rem; }}
  th {{ background: #f8fafc; font-weight: 600; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 6px;
    font-size: 0.75rem; font-weight: 600; }}
  .badge.ok {{ background: #dcfce7; color: #166534; }}
  .badge.fail {{ background: #fee2e2; color: #991b1b; }}
  .section-title {{ font-size: 1.2rem; margin: 2rem 0 1rem; }}
</style>
</head>
<body>
  <h1>📊 Dashboard de Evaluación — VISIR</h1>
  <p class="subtitle">Generado: {timestamp} | Commit: {commit}</p>

  <div class="grid">
    <div class="card">
      <h2>Recall@1</h2>
      <div class="value {recall1_class}">{recall1_pct}</div>
    </div>
    <div class="card">
      <h2>Recall@3</h2>
      <div class="value {recall3_class}">{recall3_pct}</div>
    </div>
    <div class="card">
      <h2>Routing (léxico)</h2>
      <div class="value {routing_class}">{routing_pct}</div>
    </div>
    <div class="card">
      <h2>Confianza (acción)</h2>
      <div class="value {confianza_class}">{confianza_pct}</div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Preguntas evaluadas</h2>
      <div class="value">{total_preguntas}</div>
    </div>
    <div class="card">
      <h2>Tokens totales (entrada)</h2>
      <div class="value">{tokens_entrada}</div>
    </div>
    <div class="card">
      <h2>Tokens totales (salida)</h2>
      <div class="value">{tokens_salida}</div>
    </div>
    <div class="card">
      <h2>Latencia promedio</h2>
      <div class="value">{latencia_prom}ms</div>
    </div>
  </div>

  <h2 class="section-title">Detalle por caso (Confianza)</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Descripción</th>
        <th>Score</th>
        <th>Acción</th>
        <th>Esperada</th>
        <th>Rango</th>
      </tr>
    </thead>
    <tbody>
      {confianza_rows}
    </tbody>
  </table>

  <p class="subtitle" style="margin-top: 2rem;">
    ⚠️ Dataset provisional — debe re-validarse cuando llegue el contador.
    <a href="https://github.com/anomalyco/VISIR-Backend/tree/main/evaluaciones">Ver README</a>
  </p>
</body>
</html>
"""


def _color_clase(valor: float, bueno: float = 0.70, regular: float = 0.50) -> str:
    if valor >= bueno:
        return "pass"
    if valor >= regular:
        return "warn"
    return "fail"


def _pct(valor: float) -> str:
    return f"{valor:.1%}"


def _badge(ok: bool) -> str:
    return (
        '<span class="badge ok">✅ OK</span>' if ok else '<span class="badge fail">❌ FALLA</span>'
    )


def buscar_metricas(output_dir: Path) -> dict:
    metrics_path = output_dir / "metrics_summary.json"
    if metrics_path.exists():
        return dict(json.loads(metrics_path.read_text(encoding="utf-8")))

    # Fallback: buscar el JSON de evaluación más reciente
    jsons = sorted(output_dir.glob("eval_*.json"), key=os.path.getmtime, reverse=True)
    if jsons:
        data = json.loads(jsons[0].read_text(encoding="utf-8"))
        recall = data.get("recall_global", {})
        routing_data = data.get("enrutamiento", {})
        confianza_data = data.get("confianza", {})
        return {
            "recall_at_1": recall.get("recall_at_1", 0),
            "recall_at_3": recall.get("recall_at_3", 0),
            "recall_at_5": recall.get("recall_at_5", 0),
            "total_preguntas": recall.get("total_preguntas", 0),
            "routing_precision": routing_data.get("precision", 0),
            "confianza_precision": confianza_data.get("precision_accion", 0),
            "confianza_detalle": confianza_data.get("detalle", []),
            "tokens_entrada": sum(r.get("tokens_entrada", 0) for r in data.get("resultados", [])),
            "tokens_salida": sum(r.get("tokens_salida", 0) for r in data.get("resultados", [])),
            "latencias": [],
        }

    return {}


def generar(output_dir: Path) -> str:
    m = buscar_metricas(output_dir)

    recall1 = m.get("recall_at_1", 0)
    recall3 = m.get("recall_at_3", 0)
    routing = m.get("routing_precision", 0)
    confianza = m.get("confianza_precision", 0)
    detalle_conf = m.get("confianza_detalle", [])

    confianza_rows = ""
    for d in detalle_conf:
        acc_ok = d.get("accion_ok", False)
        conf_ok = d.get("confianza_ok", False)
        confianza_rows += (
            f"<tr>"
            f"<td>{d.get('id', '')}</td>"
            f"<td>{d.get('descripcion', '')}</td>"
            f"<td>{d.get('score', 0):.4f}</td>"
            f"<td>{_badge(acc_ok)} {d.get('accion', '')}</td>"
            f"<td>{d.get('accion_esperada', '')}</td>"
            f"<td>{_badge(conf_ok)} {d.get('confianza_rango', '')}</td>"
            f"</tr>\n"
        )

    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        commit=os.environ.get("GITHUB_SHA", "local")[:7],
        recall1_pct=_pct(recall1),
        recall1_class=_color_clase(recall1),
        recall3_pct=_pct(recall3),
        recall3_class=_color_clase(recall3),
        routing_pct=_pct(routing),
        routing_class=_color_clase(routing, bueno=0.80, regular=0.60),
        confianza_pct=_pct(confianza),
        confianza_class=_color_clase(confianza, bueno=0.80, regular=0.60),
        total_preguntas=m.get("total_preguntas", 0),
        tokens_entrada=m.get("tokens_entrada", 0),
        tokens_salida=m.get("tokens_salida", 0),
        latencia_prom=0,
        confianza_rows=confianza_rows,
    )

    dashboard_path = output_dir / "dashboard.html"
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(html, encoding="utf-8")
    print(f"[DASHBOARD] Generado: {dashboard_path}")
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera dashboard HTML de evaluación VISIR")
    parser.add_argument("--output-dir", default="validation_results")
    args = parser.parse_args()

    output_dir = _ROOT / args.output_dir
    generar(output_dir)


if __name__ == "__main__":
    main()
