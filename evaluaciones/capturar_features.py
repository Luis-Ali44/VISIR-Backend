from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

from app.services.confidence_features import (  # noqa: E402
    data_completeness,
    detectar_periodo,
    detectar_tipo_consulta,
    question_clarity,
    rag_coverage,
    routing_certainty,
)

ID_ORGANIZACION_PRUEBA = "11111111-1111-1111-1111-111111111111"


def cargar_servicio() -> Any:
    from app.services.rag_service import RAGServiceLangGraph
    from rag.chain import FiscalRAGChain
    from rag.config import load_config_from_env
    from rag.retriever import FiscalRAGRetriever

    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        print("[ERROR] GROQ_API_KEY no configurada.")
        sys.exit(1)

    config = load_config_from_env(os.getenv("CHROMA_PATH", "./chroma_db"))
    modelo = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

    chain = FiscalRAGChain(api_key=groq_api_key, model=modelo, base_url=base_url)
    retriever = FiscalRAGRetriever(config)
    return RAGServiceLangGraph(
        chain=chain,
        retriever=retriever,
        llm_api_key=groq_api_key,
        llm_base_url=base_url,
        llm_model=modelo,
        rag_config=config,
    )


def capturar_fila(servicio: Any, item: dict) -> dict:
    pregunta = item["pregunta"]
    t0 = time.perf_counter()

    respuesta_final, ruta, metadata = servicio.ejecutar_consulta(
        pregunta=pregunta,
        usuario_id="eval",
        id_organizacion=item.get("_id_organizacion_prueba", ID_ORGANIZACION_PRUEBA),
        top_k=5,
    )
    latencia_ms = (time.perf_counter() - t0) * 1000

    fuentes = metadata.get("fuentes_recuperadas", [])
    palabras = metadata.get("palabras_clave", [])
    periodo = detectar_periodo(pregunta)
    tipo = detectar_tipo_consulta(pregunta)

    return {
        "id": item.get("id", pregunta[:30]),
        "pregunta": pregunta,
        "respuesta_esperada": item["respuesta_esperada"],
        "fragmentos_fuente": item.get("fragmentos_fuente", []),
        "nivel_ambiguedad": item.get("nivel_ambiguedad"),
        "accion_esperada": item.get("accion_esperada", "responder"),
        "nota": item.get("nota"),
        "es_ambigua": item.get("es_ambigua", item.get("nivel_ambiguedad") not in (None, "clara")),
        "campo_removido": item.get("campo_removido"),
        "rag_coverage": round(rag_coverage(fuentes), 4),
        "routing_certainty": round(routing_certainty(palabras), 4),
        "question_clarity": round(question_clarity(pregunta), 4),
        "data_completeness": round(data_completeness(len(fuentes), periodo["detectado"]), 4),
        "campo_periodo_faltante": item.get("campo_periodo_faltante", int(not periodo["detectado"])),
        "campo_tipo_faltante": item.get("campo_tipo_faltante", int(not tipo["detectado"])),
        "respuesta_generada": respuesta_final or "",
        "fragmentos_recuperados": fuentes,
        "ruta_seleccionada": ruta,
        "latencia_ms": round(latencia_ms, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fase 2 de V-10: captura de features")
    parser.add_argument(
        "--dataset",
        default="evaluaciones/data/dataset_confianza_gradual.json",
        help="Ruta al dataset de entrenamiento (default: dataset gradual con CFDIs reales)",
    )
    parser.add_argument(
        "--output",
        default="evaluaciones/data/dataset_confianza_features.json",
    )
    args = parser.parse_args()

    dataset_path = _ROOT / args.dataset
    if not dataset_path.exists():
        print(f"[ERROR] No existe el dataset: {dataset_path}")
        sys.exit(1)
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    print(f"[DATASET] {dataset_path.name} -- {len(dataset)} preguntas")

    servicio = cargar_servicio()

    filas = []
    errores = []
    for i, item in enumerate(dataset, 1):
        print(f"[{i}/{len(dataset)}] {item['pregunta'][:60]}")
        try:
            filas.append(capturar_fila(servicio, item))
        except Exception as e:
            print(f"  [ERROR] {e}")
            errores.append({"idx": i, "pregunta": item["pregunta"], "error": str(e)})
            continue

    output_path = _ROOT / args.output
    output_path.write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {len(filas)}/{len(dataset)} filas guardadas en {output_path}")

    if errores:
        print(f"[WARN] {len(errores)} preguntas fallaron:")
        for err_item in errores:
            err_msg = str(err_item["error"])[:80]
            print(f"       [{err_item['idx']}] {err_item['pregunta'][:50]} - {err_msg}")

    if filas:
        niveles = sorted(
            {
                f.get("nivel_ambiguedad") or ("ambigua" if f["es_ambigua"] else "clara")
                for f in filas
            }
        )
        for nivel in niveles:
            grupo = [
                f
                for f in filas
                if (f.get("nivel_ambiguedad") or ("ambigua" if f["es_ambigua"] else "clara"))
                == nivel
            ]
            if not grupo:
                continue
            rc_avg = sum(f["rag_coverage"] for f in grupo) / len(grupo)
            rt_avg = sum(f["routing_certainty"] for f in grupo) / len(grupo)
            qc_avg = sum(f["question_clarity"] for f in grupo) / len(grupo)
            dc_avg = sum(f["data_completeness"] for f in grupo) / len(grupo)
            print(f"\n--- nivel_ambiguedad={nivel} ({len(grupo)} preguntas) ---")
            print(f"   rag_coverage:       {rc_avg:.4f}")
            print(f"   routing_certainty:  {rt_avg:.4f}")
            print(f"   question_clarity:   {qc_avg:.4f}")
            print(f"   data_completeness:  {dc_avg:.4f}")


if __name__ == "__main__":
    main()
