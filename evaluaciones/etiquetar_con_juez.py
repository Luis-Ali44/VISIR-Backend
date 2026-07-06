from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from evaluaciones.juez import JuezFiscal  # noqa: E402


INPUT_PATH = _ROOT / "evaluaciones/data/dataset_confianza_features.json"
OUTPUT_PATH = _ROOT / "evaluaciones/data/dataset_confianza_final.json"
ERROR_LOG = _ROOT / "evaluaciones/data/errores_etiquetado.json"


def main() -> None:
    if not INPUT_PATH.exists():
        print(f"[ERROR] No existe el archivo de features: {INPUT_PATH}")
        print("Ejecuta primero capturar_features.py")
        sys.exit(1)

    dataset_features = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"[DATASET] {INPUT_PATH.name} -- {len(dataset_features)} preguntas")

    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        print("[ERROR] GROQ_API_KEY no configurada.")
        sys.exit(1)

    modelo = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

    juez = JuezFiscal(api_key=groq_api_key, model=modelo, base_url=base_url)

    etiquetados = []
    errores = []

    for i, item in enumerate(dataset_features, 1):
        pregunta = item["pregunta"]
        accion = item.get("accion_esperada", "responder")
        print(f"[{i}/{len(dataset_features)}] {pregunta[:60]}")

        try:
            resultado = juez.evaluar_completo(
                pregunta=pregunta,
                fragmentos=item.get("fragmentos_recuperados", []),
                respuesta_generada=item.get("respuesta_generada", ""),
                respuesta_esperada=item.get("respuesta_esperada", ""),
                accion_esperada=accion,
            )
        except Exception as e:
            print(f"  [ERROR JUEZ] {e}")
            errores.append({"idx": i, "pregunta": pregunta, "error": str(e)})
            continue

        item["fidelidad_score"] = resultado["fidelidad"].get("score", 0)
        item["fidelidad_justificacion"] = resultado["fidelidad"].get("justificacion", "")
        item["relevancia_score"] = resultado["relevancia"].get("score", 0)
        item["relevancia_justificacion"] = resultado["relevancia"].get("justificacion", "")
        item["modo_relevancia"] = resultado["modo_relevancia"]
        uid = item.get("id", pregunta[:30])
        item["calidad"] = round(
            (item["fidelidad_score"] + item["relevancia_score"]) / 2 / 10, 4
        )

        fid_color = "OK" if item["fidelidad_score"] >= 7 else "BAJO"
        rel_color = "OK" if item["relevancia_score"] >= 7 else "BAJO"
        print(f"   fid={item['fidelidad_score']:>2}/10 ({fid_color})  "
              f"rel={item['relevancia_score']:>2}/10 ({rel_color})  "
              f"accion={accion}")

        etiquetados.append(item)

    OUTPUT_PATH.write_text(
        json.dumps(etiquetados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[OK] {len(etiquetados)}/{len(dataset_features)} etiquetados -> {OUTPUT_PATH}")

    if errores:
        ERROR_LOG.write_text(
            json.dumps(errores, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[WARN] {len(errores)} errores guardados en {ERROR_LOG}")

    if etiquetados:
        for nivel in ["clara", "leve", "alta"]:
            grupo = [f for f in etiquetados if f.get("nivel_ambiguedad") == nivel]
            if not grupo:
                continue
            fid_avg = sum(f["fidelidad_score"] for f in grupo) / len(grupo)
            rel_avg = sum(f["relevancia_score"] for f in grupo) / len(grupo)
            cal_avg = sum(f["calidad"] for f in grupo) / len(grupo)
            print(f"\n--- nivel={nivel} ({len(grupo)} preguntas) ---")
            print(f"   fidelidad:   {fid_avg:>6.2f}/10")
            print(f"   relevancia:  {rel_avg:>6.2f}/10")
            print(f"   calidad:     {cal_avg:>6.4f}")

        altas = [f for f in etiquetados if f.get("nivel_ambiguedad") == "alta"]
        if altas:
            errantes = [f for f in altas if f.get("accion_esperada") != "preguntar"]
            if errantes:
                print(f"\n[CHECK] {len(errantes)} casos 'alta' sin accion_esperada='preguntar':")
                for e in errantes:
                    print(f"        {e.get('id', '?')}: {e.get('accion_esperada', '?')}")


if __name__ == "__main__":
    main()
