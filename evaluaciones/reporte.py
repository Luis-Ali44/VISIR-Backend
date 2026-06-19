from __future__ import annotations

from datetime import datetime
from pathlib import Path

from metricas import ResultadoRecall


def _emoji_score(score: int | float | None) -> str:
    """Convierte score 1-5 a emoji de semáforo."""
    if score is None:
        return "⚪"
    s = int(round(score))
    if s >= 4:
        return "🟢"
    if s == 3:
        return "🟡"
    return "🔴"


def _hit_emoji(hit: bool) -> str:
    return "✅" if hit else "❌"


def generar_reporte(
    resultados: list[dict],
    recall: ResultadoRecall,
    recall_por_dif: dict[str, ResultadoRecall] | None = None,
    modo: str = "completo",
    modelo_rag: str = "N/A",
    modelo_juez: str = "N/A",
    output_path: str | None = None,
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lineas: list[str] = []
    lineas += [
        "# Reporte de Evaluación — Sistema RAG Fiscal",
        "",
        f"**Fecha:** {ts}  ",
        f"**Modo:** `{modo}`  ",
        f"**Modelo RAG:** `{modelo_rag}`  ",
        f"**Modelo Juez:** `{modelo_juez if modo == 'completo' else 'N/A (modo recall)'}`  ",
        f"**Total preguntas evaluadas:** {recall.total_preguntas}",
        "",
        "---",
        "",
    ]

    lineas += [
        "## Resumen Ejecutivo",
        "",
        "### Recall@k — Calidad del Retriever",
        "",
        "| Métrica | Valor | Hits |",
        "|---------|-------|------|",
        f"| Recall@1 | **{recall.recall_at_1:.2%}** | {recall.hits_by_k.get(1, 0)}/{recall.total_preguntas} |",
        f"| Recall@3 | **{recall.recall_at_3:.2%}** | {recall.hits_by_k.get(3, 0)}/{recall.total_preguntas} |",
        f"| Recall@5 | **{recall.recall_at_5:.2%}** | {recall.hits_by_k.get(5, 0)}/{recall.total_preguntas} |",
        "",
    ]

    if modo == "completo":
        scores_fidelidad = [
            r["fidelidad_score"] for r in resultados
            if r.get("fidelidad_score") is not None
        ]
        scores_relevancia = [
            r["relevancia_score"] for r in resultados
            if r.get("relevancia_score") is not None
        ]
        media_fid = sum(scores_fidelidad) / len(scores_fidelidad) if scores_fidelidad else 0
        media_rel = sum(scores_relevancia) / len(scores_relevancia) if scores_relevancia else 0

        fidelidad_critica = sum(1 for s in scores_fidelidad if s < 3)
        relevancia_critica = sum(1 for s in scores_relevancia if s < 3)

        lineas += [
            "### Calidad del Generador (Modelo como Juez)",
            "",
            "| Métrica | Media | Preguntas críticas (< 3) |",
            "|---------|-------|--------------------------|",
            f"| Fidelidad | **{media_fid:.2f} / 5** {_emoji_score(media_fid)} | {fidelidad_critica} |",
            f"| Relevancia | **{media_rel:.2f} / 5** {_emoji_score(media_rel)} | {relevancia_critica} |",
            "",
        ]


    if recall_por_dif:
        lineas += [
            "### Recall@3 por Dificultad",
            "",
            "| Dificultad | Recall@1 | Recall@3 | Recall@5 | n |",
            "|-----------|----------|----------|----------|---|",
        ]
        for dif, r in sorted(recall_por_dif.items()):
            lineas.append(
                f"| {dif.capitalize()} | {r.recall_at_1:.2%} | "
                f"{r.recall_at_3:.2%} | {r.recall_at_5:.2%} | {r.total_preguntas} |"
            )
        lineas.append("")

    lineas += ["---", ""]


    lineas += ["## Detalle por Pregunta", ""]

    for i, r in enumerate(resultados, 1):
        hit_1 = r.get("hit_at_1", False)
        hit_3 = r.get("hit_at_3", False)
        hit_5 = r.get("hit_at_5", False)
        dif = r.get("dificultad", "N/A")
        pregunta = r.get("pregunta", "N/A")

        lineas += [
            f"### Pregunta {i} · Dificultad: `{dif}`",
            "",
            f"**{pregunta}**",
            "",
            "| Métrica | Resultado |",
            "|---------|-----------|",
            f"| Recall@1 | {_hit_emoji(hit_1)} {'Hit' if hit_1 else 'Miss'} |",
            f"| Recall@3 | {_hit_emoji(hit_3)} {'Hit' if hit_3 else 'Miss'} |",
            f"| Recall@5 | {_hit_emoji(hit_5)} {'Hit' if hit_5 else 'Miss'} |",
        ]

        if modo == "completo":
            fid_score = r.get("fidelidad_score")
            rel_score = r.get("relevancia_score")
            fid_razon = r.get("fidelidad_razonamiento", "")
            rel_razon = r.get("relevancia_razonamiento", "")

            lineas += [
                f"| Fidelidad | {_emoji_score(fid_score)} {fid_score}/5 |",
                f"| Relevancia | {_emoji_score(rel_score)} {rel_score}/5 |",
            ]
            if fid_razon:
                lineas += ["", f"> **Fidelidad:** {fid_razon}"]
            if rel_razon:
                lineas += [f"> **Relevancia:** {rel_razon}"]

        fragmentos_rec = r.get("fragmentos_recuperados", [])
        if fragmentos_rec:
            lineas += ["", "<details>", "<summary>Archivos recuperados (top-k)</summary>", ""]
            for j, fid in enumerate(fragmentos_rec[:5], 1):
                lineas.append(f"  {j}. `{fid}`")
            lineas += ["", "</details>"]

        lineas += ["", "---", ""]

    lineas += [
        "## Cómo Interpretar Este Reporte",
        "",
        "- **Recall@k**: mide si el fragmento correcto aparece en los primeros k resultados del retriever.",
        "  Un Recall@1 bajo pero Recall@5 alto sugiere problemas de *ranking*, no de *cobertura*.",
        "- **Fidelidad**: detecta alucinaciones (respuestas que van más allá del contexto recuperado).",
        "  Score < 3 indica que el LLM inventó información. Revisar el prompt del sistema.",
        "- **Relevancia**: detecta respuestas tangenciales (correctas pero que no satisfacen la pregunta).",
        "  Score < 3 sugiere mejorar la fragmentación o el prompt de usuario.",
        "",
        "Para re-ejecutar este reporte:",
        "```bash",
        "python evaluaciones/run_eval.py --modo completo --dataset data/eval_dataset.json",
        "```",
        "",
        f"*Generado automáticamente el {ts}*",
    ]

    contenido = "\n".join(lineas)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[REPORTE] Guardado en {path}")

    return contenido
