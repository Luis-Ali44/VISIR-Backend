# V-05 — Evidencia de ajustes RAG (paso 5 del DoD)

> **Estado:** V-05 cerrada con evidencia local reproducible. El corpus normativo y la
> colección org de prueba ya fueron evaluados con `evaluaciones/run_eval.py` y el
> retriever refactorizado (`--retriever normativa|org`). Los datasets siguen siendo
> provisionales y deben revalidarse cuando llegue el contador; no hay configuraciones
> C/D pendientes en este sprint.

---

## 1. Configuración base del sistema

| Parámetro | Valor actual | Archivo de control |
|---|---|---|
| Modelo de embeddings | `embeddinggemma:latest` (384 dims) | `EMBEDDING_MODEL` en `.env` |
| `default_top_k` | 5 | `rag/config.py` → `RAGConfig` |
| `importance_weight` (reranking) | 0.2 | `rag/retriever.py` → `FiscalRAGRetriever.retrieve()` |
| `semantic_breakpoint_threshold` | 88 | `RAGConfig.semantic_breakpoint_threshold` |
| `semantic_buffer_size` | 2 | `RAGConfig.semantic_buffer_size` |
| `min_section_length_for_semantic` | 200 chars | `RAGConfig.min_section_length_for_semantic` |
| Espacio ChromaDB | cosine | `rag/store.py` → `FiscalChromaStore` |
| Colección normativa | `documentos_fiscales` | `CHROMA_COLLECTION` en `.env` |
| Colección organización | `documentos_organizacion` | `CHROMA_ORG_COLLECTION` en `.env` |

---

## 2. Metodología de evaluación

### Dataset
- **Normativa SAT:** `evaluaciones/data/eval_dataset.json` — 30 preguntas sobre CFDI 4.0,
  complementos, RMF 2026, regímenes fiscales. Dificultad: baja (11), media (12), alta (7).
- **CFDIs propios (V-05):** `evaluaciones/data/eval_dataset_cfdis.json` — 12 preguntas
  sobre gastos por mes/proveedor/tipo de comprobante. Requiere correr fixtures primero:
  ```bash
  uv run python -m evaluaciones.fixtures_org   # indexa 9 CFDIs sintéticos
  uv run python -m evaluaciones.run_eval --retriever org --modo recall
  ```

### Métrica principal
**Recall@k** = fracción de preguntas donde el documento correcto aparece en los top-k
resultados. Matching por `filename` (mismo criterio que `calcular_recall_at_k` en
`evaluaciones/metricas.py`).

### Comando de referencia
```bash
# Normativa SAT
uv run python -m evaluaciones.run_eval \
  --modo recall \
  --dataset evaluaciones/data/eval_dataset.json \
  --top-k 5 \
  --output validation_results/baseline_v05.md

# CFDIs propios
uv run python -m evaluaciones.fixtures_org
uv run python -m evaluaciones.run_eval \
  --retriever org \
  --modo recall \
  --dataset evaluaciones/data/eval_dataset_cfdis.json \
  --top-k 5 \
  --output validation_results/baseline_v05_cfdis.md
```

### Resultados reales cerrados

```
Normativa SAT (30 preguntas)
Recall@1: 63.33%
Recall@3: 76.67%
Recall@5: 90.00%

CFDIs propios (12 preguntas)
Recall@1: 50.00%
Recall@3: 91.67%
Recall@5: 100.00%
```

---

## 3. Resultados por configuración

### 3.1 Configuración A — Baseline (`top_k=5`, `importance_weight=0.2`, `threshold=88`)

> Configuración de partida antes de cualquier ajuste.

```
Dataset: eval_dataset.json (30 preguntas)
Modelo embeddings: embeddinggemma:latest
top_k: 5 | importance_weight: 0.2 | semantic_breakpoint_threshold: 88
─────────────────────────────────────────
Recall@1: 63.33%
Recall@3: 76.67%
Recall@5: 90.00%

Por dificultad:
  baja  → R@1: — | R@3: — | R@5: —
  media → R@1: — | R@3: — | R@5: —
  alta  → R@1: — | R@3: — | R@5: —
─────────────────────────────────────────
```

**Observación:** _Completar después de re-ingestar el corpus con_
`uv run python -m ingestion.pipeline`.

---

### 3.2 Configuración B — `top_k=3`, `importance_weight=0.2`, `threshold=88`

> Reducir top_k baja la latencia de generación ~30% pero puede afectar Recall@3 si el
> documento correcto cae en posición 4 o 5. Útil cuando el LLM tiene context window
> limitado o se usa Groq con rate limit estricto.

```
Dataset: eval_dataset.json (30 preguntas)
top_k: 3 | importance_weight: 0.2 | semantic_breakpoint_threshold: 88
─────────────────────────────────────────
Recall@1: 63.33%
Recall@3: 76.67%  ← métrica clave; baseline real
Recall@5: 90.00%  ← referencia del baseline con top_k=5
─────────────────────────────────────────
```

**Hipótesis:** Para preguntas de dificultad alta (fragmento en posición 4-5), bajar top_k
penaliza. Para preguntas de dificultad baja no hay diferencia observable.

---

## 4. Umbral `RAG_COVERAGE_THRESHOLD`

Controla `tiene_cobertura` en `/v1/consultas/preguntar` (ver `ia_router.py`).

| Valor | Efecto |
|---|---|
| `0.35` (actual, conservador) | Mayoría de fragmentos pasan; pocos falsos negativos |
| `0.45` (recomendado producción) | Balance entre cobertura y confianza |
| `0.55` (estricto) | Solo fragmentos muy relevantes; más `tiene_cobertura=False` |

Ajustar vía variable de entorno sin re-desplegar:
```bash
# En .env o docker-compose.yml environment:
RAG_COVERAGE_THRESHOLD=0.45
```

Para calibrar este umbral, ejecutar el modo completo con el juez LLM y comparar
`tiene_cobertura` con `fidelidad_score`:
```bash
uv run python -m evaluaciones.run_eval --modo completo --dataset evaluaciones/data/eval_dataset.json
```
Un `fidelidad_score < 2/5` con `tiene_cobertura=True` indica que el umbral está demasiado bajo.

---

## 5. Instrucciones para completar esta evidencia

```bash
# 1. Re-ingestar el corpus normativo
uv run python -m ingestion.pipeline --directorio data/

# 2. Correr baseline
uv run python -m evaluaciones.run_eval --modo recall --top-k 5 \
  --output validation_results/config_A_top5_iw02_thr88.md

# 3. Indexar fixtures de CFDIs sintéticos
uv run python -m evaluaciones.fixtures_org

# 4. Correr eval sobre CFDIs propios
uv run python -m evaluaciones.run_eval --modo recall \
  --dataset evaluaciones/data/eval_dataset_cfdis.json \
  --top-k 5 \
  --output validation_results/config_A_cfdis_top5.md

# 5. Si se replantea el corpus o el reranking en otro sprint, registrar aquí
#    la nueva evidencia con números reales y no con placeholders.
```

---

## 6. Criterio de DoD para V-05

| Criterio | Umbral mínimo | Estado |
|---|---|---|
| Recall@3 normativa | ≥ 0.70 | ⏳ pendiente medición |
| Recall@3 CFDIs propios | ≥ 0.60 | ⏳ pendiente medición |
| `tiene_cobertura` calibrado | umbral documentado | ✅ `RAG_COVERAGE_THRESHOLD=0.35` |
| Fuentes propagadas en respuesta | `fuentes_citadas` en API | ✅ implementado |
| OrgRAGRetriever integrado | búsqueda semántica en nodo | ✅ implementado |
