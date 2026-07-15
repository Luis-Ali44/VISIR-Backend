# Evaluaciones — Sistema RAG Fiscal VISIR

## ⚠️ Aviso: datasets provisionales

Los datasets de esta carpeta son **provisionales** y deben **revalidarse cuando llegue el contador**, tal como marca el Gantt del proyecto. Cualquier cambio en el corpus normativo, en las reglas de negocio o en el pipeline de confianza requiere volver a medir estos datasets antes de abrir el PR final.

| Dataset | Propósito | Registros |
|---|---|---|
| `data/eval_dataset.json` | Recall@k del retriever normativa | ~30 preguntas |
| `data/eval_dataset_cfdis.json` | Recall@k del retriever de CFDIs | ~15 preguntas |
| `data/eval_ruteo.json` | Precisión del enrutador (NORMATIVA/CFDI/HÍBRIDO) | ~16 preguntas |
| `data/eval_confianza.json` | Pipeline de confianza V-10 (score + acción) | ~7 casos sintéticos |

## Pipeline de CI

Cada PR ejecuta 3 gates de calidad:

1. **`ci_gate.py`** — Recall@k del RAG normativo (umbral: Recall@3 ≥ 70%). Corre sobre ChromaDB + Ollama en CI.
2. **`eval_ruteo.py --modo lexico`** — Precisión del enrutador léxico (umbral: ≥ 80%). No necesita LLM.
3. **`eval_confianza.py --modo baseline`** — Pipeline de confianza V-10 contra features sintéticas (umbral: ≥ 80%). No necesita LLM ni ChromaDB.

Además se genera un **dashboard HTML** autocontenido con los resultados, disponible como artefacto del workflow.

## Scripts disponibles

```bash
# Recall@k del retriever (modo rápido para CI)
uv run python -m evaluaciones.ci_gate --umbral-recall-3 0.70

# Evaluación completa (con juez LLM)
uv run python -m evaluaciones.run_eval --modo completo --dataset data/eval_dataset.json

# Precisión del enrutador
uv run python -m evaluaciones.eval_ruteo --modo lexico --umbral 0.80

# Pipeline de confianza V-10
uv run python -m evaluaciones.eval_confianza --modo baseline --umbral 0.80

# Generar dashboard HTML
uv run python -m evaluaciones.generar_dashboard
```

## Dashboard

Los resultados de cada CI run se agregan en `validation_results/metrics_summary.json` y se renderizan como `dashboard.html` usando Chart.js desde CDN. El dashboard muestra:

- **Semáforo** de Recall@1, Recall@3, precisión de enrutamiento y precisión de confianza
- **Detalle** por caso de confianza (score, acción esperada vs real)
- **Advertencia** de que los datasets son provisionales

Para ver el dashboard, descargar el artefacto `reportes-evaluacion` del CI run y abrir `dashboard.html` en el navegador.