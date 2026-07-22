from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from app.services.confidence_scoring import ConfidenceScorer  # noqa: E402


def cargar_casos(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        print(f"[ERROR] Dataset no encontrado: {p}")
        sys.exit(1)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        print("[ERROR] El dataset debe ser una lista no vacia.")
        sys.exit(1)
    return data


def _resolver_model_path(args_model_path: str | None) -> str:
    if args_model_path:
        return args_model_path
    return os.getenv("MODELO_CONFIANZA_PATH", "")


def evaluar(casos: list[dict], scorer: ConfidenceScorer) -> dict:
    total = len(casos)
    aciertos_accion = 0
    aciertos_confianza = 0
    detalle = []

    for caso in casos:
        feats = caso["features"]
        score = scorer.calcular(feats)
        accion = scorer.decidir_accion(score)

        accion_ok = accion == caso["accion_esperada"]
        conf_min = caso.get("confianza_min", 0.0)
        conf_max = caso.get("confianza_max", 1.0)
        conf_ok = conf_min <= score <= conf_max

        if accion_ok:
            aciertos_accion += 1
        if conf_ok:
            aciertos_confianza += 1

        detalle.append(
            {
                "id": caso.get("id", "?"),
                "descripcion": caso.get("descripcion", ""),
                "score": round(score, 4),
                "accion": accion,
                "accion_esperada": caso["accion_esperada"],
                "accion_ok": accion_ok,
                "confianza_ok": conf_ok,
                "confianza_rango": f"[{conf_min}, {conf_max}]",
            }
        )

    precision_accion = aciertos_accion / total if total else 0.0
    precision_confianza = aciertos_confianza / total if total else 0.0

    return {
        "total": total,
        "aciertos_accion": aciertos_accion,
        "aciertos_confianza": aciertos_confianza,
        "precision_accion": round(precision_accion, 4),
        "precision_confianza": round(precision_confianza, 4),
        "detalle": detalle,
    }


def _imprimir_resultado(resultado: dict, modo: str) -> str:
    sep = "=" * 55
    lines = [
        f"\n{sep}",
        f"  EVAL CONFIANZA - modo {modo} ({resultado['total']} casos)",
        sep,
        f"  Precision accion:     {resultado['precision_accion']:.2%}  "
        f"({resultado['aciertos_accion']}/{resultado['total']})",
        f"  Precision confianza:  {resultado['precision_confianza']:.2%}  "
        f"({resultado['aciertos_confianza']}/{resultado['total']})",
        sep,
        f"\n  {'ID':>8s} {'Accion':>20s} {'Esperada':>20s} {'Score':>8s} {'Conf':>6s}",
        f"  {'-' * 60}",
    ]
    for d in resultado["detalle"]:
        conf_ok = "OK" if d["confianza_ok"] else "XX"
        lines.append(
            f"  {d['id']:>8s} {d['accion']:>20s} {d['accion_esperada']:>20s} "
            f"{d['score']:>8.4f}  {conf_ok}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua el pipeline de confianza V-10")
    parser.add_argument(
        "--modo",
        choices=["baseline", "modelo"],
        default=None,
        help="'baseline': pesos fijos; 'modelo': Ridge desde MODELO_CONFIANZA_PATH; "
        "default: auto (modelo si existe, si no baseline)",
    )
    parser.add_argument("--dataset", default="evaluaciones/data/eval_confianza.json")
    parser.add_argument(
        "--umbral",
        type=float,
        default=0.80,
        help="Precision minima de accion para salir con codigo 0",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta para guardar JSON de resultados",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Ruta al .pkl del modelo (opcional; por defecto lee MODELO_CONFIANZA_PATH env)",
    )
    args = parser.parse_args()

    model_path = _resolver_model_path(args.model_path)
    modo = args.modo

    if modo is None:
        modo = "modelo" if (model_path and Path(model_path).exists()) else "baseline"

    if modo == "modelo" and not model_path:
        print("[ERROR] modo 'modelo' requiere MODELO_CONFIANZA_PATH en entorno o --model-path")
        sys.exit(1)

    casos = cargar_casos(args.dataset)
    scorer = ConfidenceScorer(model_path=model_path if modo == "modelo" else "")
    resultado = evaluar(casos, scorer)

    output_text = _imprimir_resultado(resultado, modo)
    print(output_text)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resultado_json = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "modo": modo,
            "model_path": model_path if modo == "modelo" else None,
            "scorer_version": scorer.version,
            "umbral": args.umbral,
            "confianza": resultado,
        }
        output_path.write_text(
            json.dumps(resultado_json, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[JSON] Resultados guardados en {output_path}")

    ok = resultado["precision_accion"] >= args.umbral
    if ok:
        print(
            f"[OK] Precision de accion ({resultado['precision_accion']:.2%}) "
            f">= umbral ({args.umbral:.2%})"
        )
        sys.exit(0)
    else:
        print(
            f"[FALLA] Precision de accion ({resultado['precision_accion']:.2%}) "
            f"< umbral ({args.umbral:.2%})"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
