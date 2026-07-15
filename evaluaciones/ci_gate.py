"""
Wrapper de CI para evaluaciones/run_eval.py --modo recall.

Objetivo (V-07): que el pipeline de CI FALLE (exit code != 0) si el
Recall@3 del RAG normativo cae debajo de un umbral mínimo, en vez de
solo imprimir el número en consola como hace run_eval.py hoy.

Uso:
  uv run python -m evaluaciones.ci_gate --umbral-recall-3 0.70
  uv run python -m evaluaciones.ci_gate --umbral-recall-3 0.70 --umbral-recall-1 0.50

Se apoya en el JSON que ya genera run_eval.py (mismo formato que
`validation_results/eval_recall_<ts>.json`), así que no duplica la
lógica de recuperación: solo la ejecuta y aplica el criterio de
aprobación/rechazo.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def ejecutar_eval_recall(dataset: str, top_k: int, output_dir: str) -> Path:
    """Invoca run_eval.py --modo recall como subproceso y devuelve la ruta del JSON generado."""
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    output_path = output_dir_path / "eval_recall_ci.md"

    cmd = [
        sys.executable,
        "-m",
        "evaluaciones.run_eval",
        "--modo",
        "recall",
        "--dataset",
        dataset,
        "--top-k",
        str(top_k),
        "--output",
        str(output_path),
    ]
    print(f"[CI_GATE] Ejecutando: {' '.join(cmd)}")
    resultado = subprocess.run(cmd, check=False)
    if resultado.returncode != 0:
        print("[CI_GATE] run_eval.py terminó con error antes de calcular métricas.")
        sys.exit(1)

    return output_path.with_suffix(".json")


def evaluar_umbrales(
    json_path: Path,
    umbral_recall_1: float | None,
    umbral_recall_3: float,
    umbral_recall_5: float | None,
) -> bool:
    if not json_path.exists():
        print(f"[CI_GATE] No se encontró el reporte JSON esperado en {json_path}")
        return False

    data = json.loads(json_path.read_text(encoding="utf-8"))
    recall = data["recall_global"]

    print("\n" + "═" * 55)
    print("  CI GATE — Recall@k del RAG normativo (V-05 / V-07)")
    print("═" * 55)

    ok = True
    checks = [
        ("recall_at_1", umbral_recall_1),
        ("recall_at_3", umbral_recall_3),
        ("recall_at_5", umbral_recall_5),
    ]
    for clave, umbral in checks:
        if umbral is None:
            continue
        valor = recall[clave]
        estado = "✅ PASA" if valor >= umbral else "❌ FALLA"
        if valor < umbral:
            ok = False
        print(f"  {clave}: {valor:.2%}  (mínimo requerido: {umbral:.2%})  {estado}")

    print("═" * 55 + "\n")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gate de CI: falla el build si el Recall@k del RAG cae debajo del umbral."
    )
    parser.add_argument("--dataset", default="evaluaciones/data/eval_dataset.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output-dir", default="validation_results")
    parser.add_argument("--umbral-recall-1", type=float, default=None)
    parser.add_argument(
        "--umbral-recall-3",
        type=float,
        default=0.70,
        help="Umbral mínimo de Recall@3 para aprobar el build (default: 0.70)",
    )
    parser.add_argument("--umbral-recall-5", type=float, default=None)
    args = parser.parse_args()

    json_path = ejecutar_eval_recall(args.dataset, args.top_k, args.output_dir)
    ok = evaluar_umbrales(
        json_path,
        umbral_recall_1=args.umbral_recall_1,
        umbral_recall_3=args.umbral_recall_3,
        umbral_recall_5=args.umbral_recall_5,
    )

    if not ok:
        print("[CI_GATE] Build RECHAZADO: el Recall@k del RAG está debajo del umbral mínimo.")
        sys.exit(1)

    print("[CI_GATE] Build APROBADO.")
    sys.exit(0)


if __name__ == "__main__":
    main()
