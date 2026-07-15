FEATURES = [
    "rag_coverage",
    "routing_certainty",
    "question_clarity",
    "data_completeness",
    "campo_periodo_faltante",
    "campo_tipo_faltante",
]

BASELINE_PESOS = {
    "rag_coverage": 0.40,
    "routing_certainty": 0.30,
    "question_clarity": 0.15,
    "data_completeness": 0.15,
}

UMBRAL_RESPONDER = 0.8
UMBRAL_ADVERTENCIA = 0.5
