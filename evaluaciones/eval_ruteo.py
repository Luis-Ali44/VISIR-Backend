"""
V-07 (extensión): mide la precisión del enrutador de rag_service.py
(RAGServiceLangGraph._nodo_analisis_lexico + _nodo_validacion_llm)
contra un dataset etiquetado (evaluaciones/data/eval_ruteo.json).

Hoy el sistema mide Recall@k del retriever y fidelidad/relevancia de
la respuesta final (run_eval.py), pero NUNCA valida si la decisión
de ruta (NORMATIVA / CFDI_PROPIOS / HIBRIDO) fue correcta. Un error
de enrutamiento es silencioso: el sistema responde con confianza,
solo que con el contexto equivocado.

Modos:
  --modo lexico   → Solo evalúa el nodo léxico (gratis, determinista,
                     ideal para CI en cada PR).
  --modo completo → Evalúa léxico + fallback a LLM cuando la
                     confianza léxica es baja (usa el modelo real,
                     para sprint review / antes de mergear a main).

Uso:
  uv run python -m evaluaciones.eval_ruteo --modo lexico
  uv run python -m evaluaciones.eval_ruteo --modo completo
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from app.services.routing_logic import analizar_lexico


def _estado_base(pregunta: str) -> dict[str, object]:
    return {
        "pregunta": pregunta,
        "usuario_id": "eval",
        "id_organizacion": "eval",
        "top_k": 5,
        "ruta_seleccionada": None,
        "confianza_lexica": 0.0,
        "palabras_clave_detectadas": [],
        "decision_enrutamiento": None,
        "fragmentos_leyes": [],
        "datos_cfdi": {},
        "estadisticas_cfdi": {},
        "respuesta_final": None,
    }


def cargar_dataset(path: str) -> list[dict[str, str]]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        print(f"[ERROR] Dataset no encontrado: {dataset_path}")
        sys.exit(1)

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        print("[ERROR] El dataset debe ser una lista no vacía de objetos JSON.")
        sys.exit(1)

    errores = []
    for i, item in enumerate(data):
        for campo in ("pregunta", "ruta_esperada"):
            if campo not in item:
                errores.append(f"  Item {i + 1}: falta el campo '{campo}'")

    if errores:
        print("[ERROR] Problemas en el dataset:")
        for error in errores:
            print(error)
        sys.exit(1)

    print(f"[DATASET] {len(data)} preguntas etiquetadas cargadas desde {dataset_path.name}")
    return data


def evaluar_lexico(dataset: list[dict[str, str]]) -> tuple[float, list[dict[str, object]]]:
    aciertos = 0
    detalle: list[dict[str, object]] = []

    for item in dataset:
        estado = _estado_base(item["pregunta"])
        salida = analizar_lexico(estado["pregunta"])
        ruta_predicha = salida["ruta_seleccionada"]
        confianza = float(salida["confianza_lexica"])
        escalaria = confianza < 0.85
        acierto = (not escalaria) and (ruta_predicha == item["ruta_esperada"])

        if acierto:
            aciertos += 1

        detalle.append({
            "pregunta": item["pregunta"],
            "ruta_esperada": item["ruta_esperada"],
            "ruta_predicha": ruta_predicha,
            "confianza_lexica": confianza,
            "escalaria_a_llm": escalaria,
            "acierto": acierto,
        })

    total_decididos_por_lexico = sum(1 for item in detalle if not item["escalaria_a_llm"])
    precision = aciertos / total_decididos_por_lexico if total_decididos_por_lexico else 0.0
    return precision, detalle


def evaluar_completo(dataset: list[dict[str, str]]) -> tuple[float, list[dict[str, object]]]:
    from app.services.rag_service import RAGServiceLangGraph
    from rag.chain import FiscalRAGChain
    from rag.config import load_config_from_env
    from rag.retriever import FiscalRAGRetriever

    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        print("[ERROR] GROQ_API_KEY no configurada — usa --modo lexico si solo quieres CI rápido.")
        sys.exit(1)

    config = load_config_from_env(os.getenv("CHROMA_PATH", "./chroma_db"))
    chain = FiscalRAGChain(
        api_key=groq_api_key,
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
    )
    retriever = FiscalRAGRetriever(config)
    servicio = RAGServiceLangGraph(
        chain=chain,
        retriever=retriever,
        llm_api_key=groq_api_key,
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        llm_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        rag_config=config,
    )

    aciertos = 0
    detalle: list[dict[str, object]] = []

    for item in dataset:
        estado = _estado_base(item["pregunta"])
        estado_lexico = servicio._nodo_analisis_lexico(estado)
        estado.update(estado_lexico)
        if float(estado["confianza_lexica"]) < 0.85:
            estado_llm = servicio._nodo_validacion_llm(estado)
            estado.update(estado_llm)

        ruta_predicha = estado["ruta_seleccionada"]
        acierto = ruta_predicha == item["ruta_esperada"]
        if acierto:
            aciertos += 1

        detalle.append({
            "pregunta": item["pregunta"],
            "ruta_esperada": item["ruta_esperada"],
            "ruta_predicha": ruta_predicha,
            "acierto": acierto,
        })

    precision = aciertos / len(dataset) if dataset else 0.0
    return precision, detalle


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa la precisión del enrutador de VISIR")
    parser.add_argument("--modo", choices=["lexico", "completo"], default="lexico")
    parser.add_argument("--dataset", default="evaluaciones/data/eval_ruteo.json")
    parser.add_argument("--umbral", type=float, default=0.80,
                        help="Precisión mínima requerida para que el script salga con código 0.")
    args = parser.parse_args()

    dataset = cargar_dataset(args.dataset)
    print(f"[DATASET] {len(dataset)} preguntas etiquetadas cargadas ({args.modo})")

    if args.modo == "lexico":
        precision, detalle = evaluar_lexico(dataset)
    else:
        precision, detalle = evaluar_completo(dataset)

    print("\nPregunta | Esperada | Predicha | Acierto")
    print("-" * 60)
    for item in detalle:
        print(
            f"{item['pregunta'][:40]:40s} | {item['ruta_esperada']:14s} | "
            f"{item['ruta_predicha']}{' (escala)' if item.get('escalaria_a_llm') else ''} | "
            f"{'✅' if item['acierto'] else '❌'}"
        )

    print(f"\nPrecisión de enrutamiento ({args.modo}): {precision:.2%} "
          f"(umbral mínimo: {args.umbral:.2%})")

    if precision < args.umbral:
        print("[FALLA] La precisión del enrutador está debajo del umbral mínimo.")
        sys.exit(1)

    print("[OK] Enrutador dentro del umbral esperado.")
    sys.exit(0)


if __name__ == "__main__":
    main()