from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error

from app.services.confidence_config import BASELINE_PESOS, FEATURES

# Buckets de calibración: (limite_inferior, limite_superior, etiqueta)
# Ajustable según necesidad — cambiar aquí sin tocar el resto del código.
BUCKETS = [
    (0.0, 0.5, "0-0.5"),
    (0.5, 0.7, "0.5-0.7"),
    (0.7, 0.85, "0.7-0.85"),
    (0.85, 1.0, "0.85-1.0"),
]

# Criterio de calibración: si la calidad real promedio del bucket
# [0.85-1.0] es menor a este umbral, el modelo se marca como
# descalibrado y se sugiere aplicar isotonic regression.
CALIBRACION_ACEPTACION_BUCKET_ALTO = 0.65


def _baseline_prediction(row: dict) -> float:
    score = 0.0
    for col, peso in BASELINE_PESOS.items():
        score += row.get(col, 0.0) * peso
    return score


def _mae_por_nivel(y_true: np.ndarray, y_pred: np.ndarray, niveles: list[str]) -> dict:
    unicos = sorted(set(niveles))
    result = {}
    for nivel in unicos:
        mask = np.array([n == nivel for n in niveles])
        if mask.sum() == 0:
            continue
        result[nivel] = float(mean_absolute_error(y_true[mask], y_pred[mask]))
    result["global"] = float(mean_absolute_error(y_true, y_pred))
    return result


def _check_colinealidad(X: np.ndarray, nombres: list[str]) -> None:
    corr = np.corrcoef(X.T)
    print("\n--- Matriz de correlación entre features ---")
    print(f"{'':>28s}", end="")
    for n in nombres:
        print(f"{n:>24s}", end="")
    print()
    for i, n1 in enumerate(nombres):
        print(f"{n1:>24s} ", end="")
        for j in range(len(nombres)):
            print(f"{corr[i, j]:>24.4f}", end="")
        print()

    altas = []
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            if abs(corr[i, j]) > 0.8:
                altas.append((nombres[i], nombres[j], corr[i, j]))
    if altas:
        print("\n[WARN] Correlaciones altas (>0.8) detectadas:")
        for a, b, v in altas:
            print(f"       {a} <-> {b}: {v:.4f}")
    else:
        print("\n[OK] Sin correlaciones altas entre features.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fase 4: entrenar modelo de confianza V-10")
    parser.add_argument(
        "--input",
        default="evaluaciones/data/dataset_confianza_final_combinado.json",
        help="Dataset etiquetado (salida de etiquetar_con_juez.py)",
    )
    parser.add_argument(
        "--output-dir",
        default="evaluaciones/modelos",
        help="Directorio donde guardar artefactos del modelo",
    )
    args = parser.parse_args()

    input_path = _ROOT / args.input
    if not input_path.exists():
        print(f"[ERROR] No existe: {input_path}")
        sys.exit(1)

    dataset = json.loads(input_path.read_text(encoding="utf-8"))

    # Filtrar filas con calidad nula o errores de juez
    validos = [f for f in dataset if f.get("calidad") is not None]
    descartados = len(dataset) - len(validos)
    if descartados:
        print(f"[INFO] {descartados} filas descartadas (sin calidad o error de juez)")
    if not validos:
        print("[ERROR] No hay filas válidas para entrenar.")
        sys.exit(1)
    print(f"[DATASET] {len(validos)} filas válidas de {len(dataset)} totales")

    # Preparar X, y
    X = np.array([[f.get(col, 0.0) for col in FEATURES] for f in validos], dtype=float)
    y = np.array([f["calidad"] for f in validos], dtype=float)
    niveles = [f.get("nivel_ambiguedad", "desconocido") for f in validos]

    print(f"\nFeatures ({len(FEATURES)}): {FEATURES}")
    print(f"Rango de y (calidad): [{y.min():.4f}, {y.max():.4f}]")
    print("Distribución por nivel:")
    for nivel in ["clara", "leve", "alta"]:
        n = sum(1 for nv in niveles if nv == nivel)
        print(f"  {nivel}: {n}")

    # 1. Colinealidad
    _check_colinealidad(X, FEATURES)

    # 2. LOOCV + Ridge con búsqueda de alpha
    alphas = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
    n = len(validos)
    print(f"\n--- LOOCV (n={n}) para selección de alpha ---")

    mejor_alpha = None
    mejor_mae = float("inf")
    resultados_alpha = []

    for alpha in alphas:
        maes = []
        for holdout in range(n):
            mascara = np.ones(n, dtype=bool)
            mascara[holdout] = False
            X_train, y_train = X[mascara], y[mascara]
            X_test, y_test = X[~mascara], y[~mascara]

            model = Ridge(alpha=alpha)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            maes.append(abs(y_pred[0] - y_test[0]))

        mae_prom = float(np.mean(maes))
        resultados_alpha.append((alpha, mae_prom))
        marca = " <<<" if mae_prom < mejor_mae else ""
        if mae_prom < mejor_mae:
            mejor_mae = mae_prom
            mejor_alpha = alpha
        print(f"  alpha={alpha:>8.2f}  MAE={mae_prom:.6f}{marca}")

    print(f"\n[OK] Mejor alpha: {mejor_alpha} (MAE LOOCV={mejor_mae:.6f})")

    # 3. Entrenar modelo final con mejor alpha (100% datos)
    final_model = Ridge(alpha=mejor_alpha)
    final_model.fit(X, y)
    y_pred_final = final_model.predict(X)

    # 4. Baseline de pesos fijos
    y_baseline = np.array([_baseline_prediction(f) for f in validos], dtype=float)

    # 5. Métricas
    mae_modelo = _mae_por_nivel(y, y_pred_final, niveles)
    mae_baseline = _mae_por_nivel(y, y_baseline, niveles)

    print("\n" + "=" * 60)
    print("  COMPARACIÓN: MODELO vs BASELINE (pesos fijos)")
    print("=" * 60)
    print(f"{'':>24s}  {'MODELO':>10s}  {'BASELINE':>10s}  {'DIF':>10s}")
    print(
        f"{'global':>24s}  {mae_modelo['global']:>10.4f}  {mae_baseline['global']:>10.4f}  {(mae_baseline['global'] - mae_modelo['global']):>+10.4f}"
    )
    for nivel in ["clara", "leve", "alta"]:
        m_m = mae_modelo.get(nivel, 0)
        m_b = mae_baseline.get(nivel, 0)
        print(f"{nivel:>24s}  {m_m:>10.4f}  {m_b:>10.4f}  {(m_b - m_m):>+10.4f}")

    gana = mae_modelo["global"] < mae_baseline["global"]
    print(f"\n  → Modelo {'SUPERA' if gana else 'NO SUPERA'} al baseline de pesos fijos")
    if not gana:
        print("    (con tan pocos datos es esperable — considerar usar heurística por ahora)")

    # 6. LOOCV con mejor alpha para recoger predicciones (calibración)
    print(f"\n--- LOOCV con alpha={mejor_alpha} para calibración ---")
    y_pred_loocv = np.zeros(n)
    for holdout in range(n):
        mascara = np.ones(n, dtype=bool)
        mascara[holdout] = False
        X_train, y_train = X[mascara], y[mascara]
        X_test = X[~mascara]
        model = Ridge(alpha=mejor_alpha)
        model.fit(X_train, y_train)
        y_pred_loocv[holdout] = float(model.predict(X_test)[0])

    cal_buckets = []
    print(f"\n{'Bucket':>12s}  {'n':>3s}  {'pred_prom':>9s}  {'real_prom':>9s}  {'diff':>+7s}")
    for lo, hi, label in BUCKETS:
        if hi < 1.0:
            mask = (y_pred_loocv >= lo) & (y_pred_loocv < hi)
        else:
            mask = (y_pred_loocv >= lo) & (y_pred_loocv <= hi)
        entry: dict = {"bucket": label, "rango": f"[{lo}-{hi})"}
        if mask.sum() == 0:
            entry["n"] = 0
            cal_buckets.append(entry)
            print(f"  {label:>10s}  {'0':>3s}  {'—':>9s}  {'—':>9s}  {'—':>+7s}")
            continue
        pred_prom = float(y_pred_loocv[mask].mean())
        real_prom = float(y[mask].mean())
        diff = real_prom - pred_prom
        entry.update(
            {
                "n": int(mask.sum()),
                "pred_promedio": round(pred_prom, 4),
                "real_promedio": round(real_prom, 4),
                "diferencia": round(diff, 4),
            }
        )
        cal_buckets.append(entry)
        flag = ""
        if label == "0.85-1.0" and real_prom < CALIBRACION_ACEPTACION_BUCKET_ALTO:
            flag = " <<< DESCALIBRADO"
        print(
            f"  {label:>10s}  {entry['n']:>3d}  {pred_prom:>9.4f}  {real_prom:>9.4f}  {diff:>+7.4f}{flag}"
        )

    bucket_alto = next((b for b in cal_buckets if b.get("bucket") == "0.85-1.0"), None)
    calibrado = (
        bucket_alto is not None
        and bucket_alto.get("n", 0) > 0
        and bucket_alto.get("real_promedio", 0) >= CALIBRACION_ACEPTACION_BUCKET_ALTO
    )
    print(
        f"\n  → Calibración: {'OK' if calibrado else 'DESCALIBRADO'} "
        f"(bucket alto real ≥ {CALIBRACION_ACEPTACION_BUCKET_ALTO}: {calibrado})"
    )
    if not calibrado:
        print("    Sugerencia: aplicar Platt scaling o isotonic regression post-hoc.")

    # 7. Coeficientes
    print(f"\n{'=' * 60}")
    print("  COEFICIENTES DEL MODELO RIDGE")
    print("=" * 60)
    print(f"{'Feature':>24s}  {'Coeficiente':>12s}")
    for col, coef in sorted(zip(FEATURES, final_model.coef_), key=lambda x: -abs(x[1])):
        print(f"{col:>24s}  {coef:>+12.6f}")
    print(f"{'intercept':>24s}  {final_model.intercept_:>+12.6f}")

    signos_raros = [
        col
        for col, coef in zip(FEATURES, final_model.coef_)
        if col != "campo_periodo_faltante" and col != "campo_tipo_faltante" and coef < -0.01
    ]
    if signos_raros:
        print(f"\n[CHECK] Features con signo negativo contraintuitivo: {signos_raros}")
        print("        Investigar antes de confiar en el modelo.")

    # 8. Guardar artefactos
    output_dir = _ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    modelo_path = output_dir / "modelo_confianza_ridge.pkl"
    with open(modelo_path, "wb") as f:
        pickle.dump(final_model, f)

    umbrales_accion = {}
    try:
        p80 = float(np.percentile(y_pred_loocv, 80))
        p50 = float(np.percentile(y_pred_loocv, 50))
        umbrales_accion = {
            "responder_desde": round(p80, 4),
            "advertencia_desde": round(p50, 4),
            "preguntar_desde": 0.0,
        }
    except Exception:
        umbrales_accion = {"responder_desde": 0.8, "advertencia_desde": 0.5, "preguntar_desde": 0.0}

    reporte = {
        "dataset": str(input_path),
        "n_filas_validas": len(validos),
        "n_descartadas": descartados,
        "features": FEATURES,
        "mejor_alpha": mejor_alpha,
        "mae_loocv": mejor_mae,
        "mae_modelo_global": mae_modelo["global"],
        "mae_baseline_global": mae_baseline["global"],
        "modelo_supera_baseline": gana,
        "mae_por_nivel_modelo": {k: v for k, v in mae_modelo.items() if k != "global"},
        "mae_por_nivel_baseline": {k: v for k, v in mae_baseline.items() if k != "global"},
        "coeficientes": {col: float(c) for col, c in zip(FEATURES, final_model.coef_)},
        "intercepto": float(final_model.intercept_),
        "resultados_alpha": [(a, m) for a, m in resultados_alpha],
        "calibracion_buckets": cal_buckets,
        "calibracion_ok": calibrado,
        "calibracion_umbral_aceptacion": CALIBRACION_ACEPTACION_BUCKET_ALTO,
        "umbrales_accion": umbrales_accion,
    }

    reporte_path = output_dir / "reporte_entrenamiento.json"
    reporte_path.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[OK] Modelo guardado: {modelo_path}")
    print(f"[OK] Reporte guardado: {reporte_path}")

    # Copia del dataset usado para entrenar (trazabilidad)
    dataset_usado = output_dir / "dataset_usado_para_entrenar.json"
    dataset_usado.write_text(json.dumps(validos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Dataset usado guardado: {dataset_usado}")


if __name__ == "__main__":
    main()
