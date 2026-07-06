

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "evaluaciones"))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from evaluaciones.juez import JuezFiscal
from evaluaciones.metricas import (
    calcular_recall_at_k,
    calcular_recall_global,
    recall_por_dificultad,
)
from evaluaciones.reporte import generar_reporte

from rag.config import load_config_from_env
from rag.retriever import FiscalRAGRetriever, OrgRAGRetriever



def cargar_dataset(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        print(f"[ERROR] Dataset no encontrado: {p}")
        sys.exit(1)

    data = json.loads(p.read_text(encoding="utf-8"))

    if not isinstance(data, list) or not data:
        print("[ERROR] El dataset debe ser una lista no vacía de objetos JSON.")
        sys.exit(1)

    errores = []
    for i, item in enumerate(data):
        for campo in ("pregunta", "respuesta_esperada", "fragmentos_fuente"):
            if campo not in item:
                errores.append(f"  Item {i+1}: falta el campo '{campo}'")
        if "dificultad" not in item:
            item["dificultad"] = "desconocida"
        item["fragmentos_fuente"] = [f.strip() for f in item["fragmentos_fuente"]]

    if errores:
        print("[ERROR] Problemas en el dataset:")
        for e in errores:
            print(e)
        sys.exit(1)

    print(f"[DATASET] {len(data)} preguntas cargadas desde {p.name}")
    return data



def recuperar_para_evaluacion(
    retriever: FiscalRAGRetriever | OrgRAGRetriever,
    pregunta: str,
    top_k: int = 5,
    id_organizacion: str | None = None,
) -> tuple[list[str], list[str], list[dict]]:
    if isinstance(retriever, OrgRAGRetriever):
        if not id_organizacion:
            raise ValueError("id_organizacion es obligatorio para el retriever org")
        fragmentos = retriever.retrieve(query=pregunta, id_organizacion=id_organizacion, top_k=top_k, tipo_documento="cfdi")
    else:
        fragmentos = retriever.retrieve(query=pregunta, top_k=top_k)

    filenames_recuperados = [f.filename for f in fragmentos]
    chunk_ids_recuperados = [f.chunk_id for f in fragmentos]
    fragmentos_para_juez = [
        {
            "chunk_id": f.chunk_id,
            "texto": f.text,
            "fuente": f.filename,
            "seccion": f.section,
        }
        for f in fragmentos
    ]
    return filenames_recuperados, chunk_ids_recuperados, fragmentos_para_juez


def crear_retriever(config, retriever_name: str) -> FiscalRAGRetriever | OrgRAGRetriever:
    if retriever_name == "org":
        return OrgRAGRetriever(config)
    return FiscalRAGRetriever(config)


def generar_respuesta_rag(
    api_key: str,
    model: str,
    base_url: str,
    pregunta: str,
    fragmentos_raw,
) -> tuple[str, int, int]:
    from rag.chain import FiscalRAGChain
    chain = FiscalRAGChain(api_key=api_key, model=model, base_url=base_url)
    try:
        resultado = chain.invoke(pregunta=pregunta, fragmentos=fragmentos_raw)
        return resultado.texto, resultado.tokens_entrada, resultado.tokens_salida
    except Exception:
        print(f"         [WARN] Fallo generación RAG, usando fallback")
        return "El contexto disponible no cubre esta pregunta.", 0, 0



def ejecutar_evaluacion(args: argparse.Namespace) -> None:
    t_inicio = time.time()
    modo = args.modo
    top_k = args.top_k
    retriever_name = args.retriever
    org_id = args.org_id

    print(f"\n{'═'*65}")
    print(f"  EVALUACIÓN RAG FISCAL — Modo: {modo.upper()}")
    print(f"  Dataset: {args.dataset}")
    print(f"  top_k: {top_k}")
    print(f"  Matching: por nombre de archivo (fragmentos_fuente)")
    print(f"{'═'*65}\n")


    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    config = load_config_from_env(chroma_path=chroma_path)
    retriever = crear_retriever(config, retriever_name)

    groq_api_key   = os.getenv("GROQ_API_KEY", "")
    groq_model     = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_judge_model = os.getenv("GROQ_JUDGE_MODEL", "llama-3.3-70b-versatile")
    llm_base_url   = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

    if modo == "completo" and not groq_api_key:
        print("[ERROR] GROQ_API_KEY no configurada en .env")
        sys.exit(1)

    dataset = cargar_dataset(args.dataset)

    juez = None
    if modo == "completo":
        print(f"[JUEZ] Inicializando con modelo: {groq_judge_model}")
        juez = JuezFiscal(
            api_key=groq_api_key,
            model=groq_judge_model,
            base_url=llm_base_url,
        )

    resultados: list[dict] = []
    datos_recall: list[dict] = []

    for i, item in enumerate(dataset, 1):
        pregunta          = item["pregunta"]
        respuesta_esperada = item["respuesta_esperada"]
        fuentes_esperadas = item["fragmentos_fuente"]
        dificultad        = item["dificultad"]

        print(f"\n[{i:02d}/{len(dataset)}] {pregunta[:70]}...")
        print(f"         Fuentes esperadas: {fuentes_esperadas}")

        t0 = time.time()
        filenames_rec, chunk_ids_rec, fragmentos_para_juez = recuperar_para_evaluacion(
            retriever,
            pregunta,
            top_k=top_k,
            id_organizacion=org_id,
        )
        lat_rec = round((time.time() - t0) * 1000)

        hit_1 = calcular_recall_at_k(fuentes_esperadas, filenames_rec, k=1)
        hit_3 = calcular_recall_at_k(fuentes_esperadas, filenames_rec, k=3)
        hit_5 = calcular_recall_at_k(fuentes_esperadas, filenames_rec, k=5)

        archivos_unicos = list(dict.fromkeys(filenames_rec))
        print(f"         Archivos top-{top_k}: {archivos_unicos}")
        print(f"         Recall → @1:{int(hit_1)} @3:{int(hit_3)} @5:{int(hit_5)}  ({lat_rec}ms)")

        datos_recall.append({
            "fuentes_esperadas": fuentes_esperadas,
            "fuentes_recuperadas": filenames_rec,
            "dificultad": dificultad,
        })

        resultado_item: dict = {
            "pregunta": pregunta,
            "dificultad": dificultad,
            "fuentes_esperadas": fuentes_esperadas,
            "filenames_recuperados": filenames_rec,
            "chunk_ids_recuperados": chunk_ids_rec,
            "hit_at_1": hit_1,
            "hit_at_3": hit_3,
            "hit_at_5": hit_5,
            "latencia_recuperacion_ms": lat_rec,
        }

        if modo == "completo" and juez is not None:
            if isinstance(retriever, OrgRAGRetriever):
                fragmentos_raw = retriever.retrieve(query=pregunta, id_organizacion=org_id, top_k=top_k, tipo_documento="cfdi")
            else:
                fragmentos_raw = retriever.retrieve(query=pregunta, top_k=top_k)

            t1 = time.time()
            respuesta_generada, tokens_entrada, tokens_salida = generar_respuesta_rag(
                api_key=groq_api_key,
                model=groq_model,
                base_url=llm_base_url,
                pregunta=pregunta,
                fragmentos_raw=fragmentos_raw,
            )
            lat_gen = round((time.time() - t1) * 1000)

            t2 = time.time()
            try:
                eval_completo = juez.evaluar_completo(
                    pregunta=pregunta,
                    fragmentos=fragmentos_para_juez,
                    respuesta_generada=respuesta_generada,
                    respuesta_esperada=respuesta_esperada,
                    accion_esperada=item.get("accion_esperada"),
                )
                eval_fidelidad = eval_completo["fidelidad"]
                eval_relevancia = eval_completo["relevancia"]
                fid_score = eval_fidelidad.get("score", 0)
                rel_score = eval_relevancia.get("score", 0)
            except Exception as e:
                print(f"         [WARN] Juez falló: {e}")
                eval_fidelidad = {"score": 0, "razonamiento": "", "fallo": str(e)}
                eval_relevancia = {"score": 0, "razonamiento": "", "fallo": str(e)}
                fid_score = 0
                rel_score = 0

            lat_juez = round((time.time() - t2) * 1000)

            print(f"         Tokens → entrada:{tokens_entrada}  salida:{tokens_salida}")
            print(f"         Juez → Fidelidad:{fid_score}/10  Relevancia:{rel_score}/10  ({lat_juez}ms)")

            resultado_item.update({
                "respuesta_generada": respuesta_generada,
                "respuesta_esperada": respuesta_esperada,
                "tokens_entrada": tokens_entrada,
                "tokens_salida": tokens_salida,
                "fidelidad_score": fid_score,
                "fidelidad_razonamiento": eval_fidelidad.get("razonamiento", ""),
                "fidelidad_detalle": eval_fidelidad,
                "relevancia_score": rel_score,
                "relevancia_razonamiento": eval_relevancia.get("razonamiento", ""),
                "relevancia_detalle": eval_relevancia,
                "calidad": round((fid_score + rel_score) / 2 / 10, 4),
                "latencia_generacion_ms": lat_gen,
                "latencia_juez_ms": lat_juez,
            })

        resultados.append(resultado_item)

    recall_global = calcular_recall_global(datos_recall)
    recall_dif    = recall_por_dificultad(datos_recall)

    elapsed = round(time.time() - t_inicio, 1)
    print(f"\n{'─'*65}")
    print(f"  RESULTADOS GLOBALES  ({elapsed}s total, {len(dataset)} preguntas)")
    print(f"{'─'*65}")
    print(f"  Recall@1: {recall_global.recall_at_1:.2%}  "
          f"({recall_global.hits_by_k.get(1,0)}/{recall_global.total_preguntas})")
    print(f"  Recall@3: {recall_global.recall_at_3:.2%}  "
          f"({recall_global.hits_by_k.get(3,0)}/{recall_global.total_preguntas})")
    print(f"  Recall@5: {recall_global.recall_at_5:.2%}  "
          f"({recall_global.hits_by_k.get(5,0)}/{recall_global.total_preguntas})")

    if modo == "completo":
        scores_fid = [r["tokens_entrada"] for r in resultados if "tokens_entrada" in r]
        total_tokens_entrada = sum(r.get("tokens_entrada", 0) for r in resultados)
        total_tokens_salida  = sum(r.get("tokens_salida", 0) for r in resultados)
        scores_fid_eval = [r["fidelidad_score"] for r in resultados if "fidelidad_score" in r]
        scores_rel = [r["relevancia_score"] for r in resultados if "relevancia_score" in r]
        if scores_fid_eval:
            print(f"  Fidelidad media:  {sum(scores_fid_eval)/len(scores_fid_eval):.2f}/10")
        if scores_rel:
            print(f"  Relevancia media: {sum(scores_rel)/len(scores_rel):.2f}/10")
        print(f"  Tokens totales → entrada:{total_tokens_entrada}  salida:{total_tokens_salida}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or f"validation_results/eval_{modo}_{ts}.md"

    generar_reporte(
        resultados=resultados,
        recall=recall_global,
        recall_por_dif=recall_dif,
        modo=modo,
        modelo_rag=groq_model,
        modelo_juez=groq_judge_model if modo == "completo" else "N/A",
        output_path=output_path,
    )

    json_path = Path(output_path).with_suffix(".json")
    json_path.write_text(
        json.dumps({
            "timestamp": datetime.now().isoformat(),
            "modo": modo,
            "modelo_rag": groq_model,
            "modelo_juez": groq_judge_model,
            "top_k": top_k,
            "recall_global": recall_global.as_dict(),
            "recall_por_dificultad": {k: v.as_dict() for k, v in recall_dif.items()},
            "resultados": resultados,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[JSON]    Guardado en {json_path}")
    print(f"{'═'*65}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluación del sistema RAG Fiscal")
    parser.add_argument(
        "--modo", choices=["recall", "completo"], default="recall",
        help="recall: solo Recall@k (para CI). completo: + juez LLM (para sprint review).",
    )
    parser.add_argument(
        "--retriever", choices=["normativa", "org"], default="normativa",
        help="Selecciona la colección a evaluar: normativa SAT o CFDIs de organización.",
    )
    parser.add_argument(
        "--org-id", default="11111111-1111-1111-1111-111111111111",
        help="id_organizacion usado cuando --retriever org.",
    )
    parser.add_argument(
        "--dataset", default=None,
        help="Ruta al dataset de evaluación.",
    )
    parser.add_argument(
        "--top-k", type=int, default=5, dest="top_k",
        help="Número de fragmentos a recuperar (default: 5).",
    )
    parser.add_argument(
        "--output", default=None,
        help="Ruta del reporte Markdown (default: validation_results/eval_<ts>.md).",
    )
    args = parser.parse_args()
    if args.dataset is None:
        args.dataset = (
            "evaluaciones/data/eval_dataset_cfdis.json"
            if args.retriever == "org"
            else "evaluaciones/data/eval_dataset.json"
        )
    ejecutar_evaluacion(args)


if __name__ == "__main__":
    main()
