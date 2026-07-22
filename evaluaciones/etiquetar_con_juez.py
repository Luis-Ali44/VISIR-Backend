from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

from evaluaciones.juez import JuezFiscal  # noqa: E402


def _esperar_429(error_msg: str) -> float | None:
    match = re.search(r"Please try again in (\d+)m([\d.]+)?s", error_msg)
    if match:
        minutos = int(match.group(1))
        segundos = float(match.group(2) or 0)
        return minutos * 60 + segundos
    match = re.search(r"Please try again in ([\d.]+)s", error_msg)
    if match:
        return float(match.group(1))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Fase 3: etiquetar features con juez LLM")
    parser.add_argument(
        "--input",
        default="evaluaciones/data/dataset_confianza_features.json",
    )
    parser.add_argument(
        "--output",
        default="evaluaciones/data/dataset_confianza_final.json",
    )
    args = parser.parse_args()

    input_path = _ROOT / args.input
    output_path = _ROOT / args.output
    error_log = output_path.with_stem(output_path.stem + "_errores").with_suffix(".json")

    if not input_path.exists():
        print(f"[ERROR] No existe el archivo de features: {input_path}")
        print("Ejecuta primero capturar_features.py")
        sys.exit(1)

    dataset_features = json.loads(input_path.read_text(encoding="utf-8"))
    print(f"[DATASET] {input_path.name} -- {len(dataset_features)} preguntas")

    etiquetados: list[dict] = []
    errores: list[dict] = []
    ids_procesados: set[str] = set()

    if output_path.exists():
        etiquetados = json.loads(output_path.read_text(encoding="utf-8"))
        ids_procesados = {item.get("id", "") for item in etiquetados}
        print(
            f"[REANUDANDO] {len(etiquetados)} filas ya procesadas, "
            f"{len(dataset_features) - len(ids_procesados)} pendientes"
        )

    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        print("[ERROR] GROQ_API_KEY no configurada.")
        sys.exit(1)

    modelo = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

    juez = JuezFiscal(api_key=groq_api_key, model=modelo, base_url=base_url)

    for i, item in enumerate(dataset_features, 1):
        item_id = item.get("id", item["pregunta"][:30])

        if item_id in ids_procesados:
            print(
                f"[{i}/{len(dataset_features)}] {item['pregunta'][:60]} -- ya procesado, saltando"
            )
            continue

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
            error_str = str(e)
            espera = _esperar_429(error_str)
            if espera is not None:
                print(f"  [429] Cuota excedida, esperando {espera:.0f}s antes de reintentar...")
                time.sleep(espera + 2)
                try:
                    resultado = juez.evaluar_completo(
                        pregunta=pregunta,
                        fragmentos=item.get("fragmentos_recuperados", []),
                        respuesta_generada=item.get("respuesta_generada", ""),
                        respuesta_esperada=item.get("respuesta_esperada", ""),
                        accion_esperada=accion,
                    )
                except Exception as e2:
                    print(f"  [ERROR JUEZ] {e2}")
                    errores.append(
                        {"idx": i, "id": item_id, "pregunta": pregunta, "error": str(e2)}
                    )
                    continue
            else:
                print(f"  [ERROR JUEZ] {error_str[:200]}")
                errores.append({"idx": i, "id": item_id, "pregunta": pregunta, "error": error_str})
                continue

        item["fidelidad_score"] = resultado["fidelidad"].get("score", 0)
        item["fidelidad_justificacion"] = resultado["fidelidad"].get("justificacion", "")
        item["relevancia_score"] = resultado["relevancia"].get("score", 0)
        item["relevancia_justificacion"] = resultado["relevancia"].get("justificacion", "")
        item["modo_relevancia"] = resultado["modo_relevancia"]
        item["calidad"] = round((item["fidelidad_score"] + item["relevancia_score"]) / 2 / 10, 4)

        fid_color = "OK" if item["fidelidad_score"] >= 7 else "BAJO"
        rel_color = "OK" if item["relevancia_score"] >= 7 else "BAJO"
        print(
            f"   fid={item['fidelidad_score']:>2}/10 ({fid_color})  "
            f"rel={item['relevancia_score']:>2}/10 ({rel_color})  "
            f"accion={accion}"
        )

        etiquetados.append(item)

        output_path.write_text(
            json.dumps(etiquetados, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"\n[OK] {len(etiquetados)}/{len(dataset_features)} etiquetados -> {output_path}")

    if errores:
        error_log.write_text(json.dumps(errores, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[WARN] {len(errores)} errores guardados en {error_log}")

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
                for err_item in errantes:
                    print(
                        f"        {err_item.get('id', '?')}: {err_item.get('accion_esperada', '?')}"
                    )


if __name__ == "__main__":
    main()
