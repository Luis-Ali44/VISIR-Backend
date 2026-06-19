"""
metricas.py
───────────
Cálculo de Recall@k para el sistema RAG fiscal.

Recall@k responde: "¿Algún fragmento del documento correcto aparece en los primeros k resultados?"

  Recall@k = preguntas donde algún fragmento del archivo esperado apareció en top-k
             ──────────────────────────────────────────────────────────────────────
                                  total de preguntas evaluadas

NOTA SOBRE fragmentos_fuente:
  Los datasets H-07 usan NOMBRES DE ARCHIVO como fragmentos_fuente
  (ej. "rfc-generico.md", "Anexo_20_Guia_Llenado_CFDI_v4_v2.pdf").
  El matching se hace contra el campo `filename` de cada RetrievalContext,
  que ChromaDB almacena como metadata durante la ingesta.

  NO se comparan chunk_ids (hashes SHA) porque esos cambiarían si se
  reingestara el corpus, haciendo el dataset frágil.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResultadoRecall:
    """Resultado de Recall@k para un conjunto de evaluaciones."""

    total_preguntas: int
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    hits_by_k: dict[int, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total_preguntas": self.total_preguntas,
            "recall_at_1": round(self.recall_at_1, 4),
            "recall_at_3": round(self.recall_at_3, 4),
            "recall_at_5": round(self.recall_at_5, 4),
        }

    def resumen_markdown(self) -> str:
        return (
            f"| Recall@1 | {self.recall_at_1:.2%} |\n"
            f"| Recall@3 | {self.recall_at_3:.2%} |\n"
            f"| Recall@5 | {self.recall_at_5:.2%} |"
        )


def calcular_recall_at_k(
    fuentes_esperadas: list[str],
    fuentes_recuperadas: list[str],
    k: int,
) -> bool:
    """
    Determina si al menos un fragmento de los documentos esperados aparece
    entre los primeros k fragmentos recuperados.
    """
    top_k_fuentes = set(fuentes_recuperadas[:k])
    esperadas = set(fuentes_esperadas)
    return bool(top_k_fuentes & esperadas)


def calcular_recall_global(
    resultados_por_pregunta: list[dict],
    ks: tuple[int, ...] = (1, 3, 5),
) -> ResultadoRecall:
    """Calcula Recall@k agregado sobre todas las preguntas del dataset."""
    total = len(resultados_por_pregunta)
    if total == 0:
        return ResultadoRecall(total_preguntas=0, recall_at_1=0.0, recall_at_3=0.0, recall_at_5=0.0)

    hits: dict[int, int] = {k: 0 for k in ks}
    for r in resultados_por_pregunta:
        esperadas = r["fuentes_esperadas"]
        recuperadas = r["fuentes_recuperadas"]
        for k in ks:
            if calcular_recall_at_k(esperadas, recuperadas, k):
                hits[k] += 1

    return ResultadoRecall(
        total_preguntas=total,
        recall_at_1=hits.get(1, 0) / total,
        recall_at_3=hits.get(3, 0) / total,
        recall_at_5=hits.get(5, 0) / total,
        hits_by_k=hits,
    )


def recall_por_dificultad(
    resultados: list[dict],
    ks: tuple[int, ...] = (1, 3, 5),
) -> dict[str, ResultadoRecall]:
    """Segmenta el Recall@k por nivel de dificultad del dataset."""
    por_dificultad: dict[str, list[dict]] = {}
    for r in resultados:
        dif = r.get("dificultad", "desconocida")
        por_dificultad.setdefault(dif, []).append(r)

    return {
        dif: calcular_recall_global(subset, ks)
        for dif, subset in sorted(por_dificultad.items())
    }
