from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from app.services.confidence_features import (  # noqa: E402
    detectar_periodo,
    detectar_tipo_consulta,
    question_clarity,
    data_completeness,
    rag_coverage,
    routing_certainty,
)


def cargar_servicio():
    from rag.chain import FiscalRAGChain
    from rag.config import load_config_from_env
    from rag.retriever import FiscalRAGRetriever
    from app.services.rag_service import RAGServiceLangGraph

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


def capturar_fila(servicio, item: dict) -> dict:
    pregunta = item["pregunta"]
    t0 = time.perf_counter()

    respuesta_final, ruta, metadata = servicio.ejecutar_consulta(
        pregunta=pregunta,
        usuario_id="eval",
        id_organizacion=item.get("_id_organizacion_prueba", "11111111-1111-1111-1111-111111111111"),
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
        "es_ambigua": item.get("es_ambigua", False),
        "campo_removido": item.get("campo_removido"),
        "rag_coverage": round(rag_coverage(fuentes), 4),
        "routing_certainty": round(routing_certainty(palabras), 4),
        "question_clarity": round(question_clarity(pregunta), 4),
        "data_completeness": round(
            data_completeness(len(fuentes), periodo["detectado"]), 4
        ),
        "campo_periodo_faltante": int(not periodo["detectado"]),
        "campo_tipo_faltante": int(not tipo["detectado"]),
        "respuesta_generada": respuesta_final or "",
        "fragmentos_recuperados": fuentes,
        "ruta_seleccionada": ruta,
        "latencia_ms": round(latencia_ms, 1),
    }


def main() -> None:
    dataset_path = _ROOT / "evaluaciones/data/dataset_confianza_variantes.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

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

    output_path = _ROOT / "evaluaciones/data/dataset_confianza_features.json"
    output_path.write_text(
        json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[OK] {len(filas)}/{len(dataset)} filas guardadas en {output_path}")

    if errores:
        print(f"[WARN] {len(errores)} preguntas fallaron:")
        for e in errores:
            err_msg = str(e['error'])[:80]
            print(f"       [{e['idx']}] {e['pregunta'][:50]} - {err_msg}")

    if filas:
        for etiqueta, es_amb in [("no_ambigua", False), ("ambigua", True)]:
            grupo = [f for f in filas if f["es_ambigua"] == es_amb]
            if not grupo:
                continue
            rc_avg = sum(f["rag_coverage"] for f in grupo) / len(grupo)
            rt_avg = sum(f["routing_certainty"] for f in grupo) / len(grupo)
            qc_avg = sum(f["question_clarity"] for f in grupo) / len(grupo)
            dc_avg = sum(f["data_completeness"] for f in grupo) / len(grupo)
            print("")
            print(f"--- {etiqueta} ({len(grupo)} preguntas) ---")
            print(f"   rag_coverage:       {rc_avg:.4f}")
            print(f"   routing_certainty:  {rt_avg:.4f}")
            print(f"   question_clarity:   {qc_avg:.4f}")
            print(f"   data_completeness:  {dc_avg:.4f}")


if __name__ == "__main__":
    main()
