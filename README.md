# VISIR API

Backend del sistema VISIR — ERP inteligente con asistente fiscal RAG.

**Stack:** FastAPI · Supabase · ChromaDB · Ollama · LangChain · uv

---

## Requisitos

| Herramienta | Versión | Verificar |
|---|---|---|
| Python | 3.12.x | `python --version` |
| uv | cualquiera | `uv --version` |
| Docker Desktop | cualquiera | `docker --version` |
| Ollama | cualquiera | `ollama --version` |

### Instalar uv

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Arranque rápido

### 1 — Clonar y configurar

```bash
git clone https://github.com/Luis-Ali44/VISIR-Backend.git
cd VISIR-Backend
cp .env.example .env
# Editar .env con tus credenciales de Supabase y API key de Groq
```

### 2 — Verificar Ollama

El sistema usa Ollama como servidor local de embeddings. Debe estar corriendo en tu máquina antes de levantar Docker.

```bash
# Verificar que Ollama responde
curl http://localhost:11434/api/tags

# Si no está corriendo, iniciarlo
ollama serve

# Verificar que tienes el modelo de embeddings
ollama list

# Si no aparece embeddinggemma, descargarlo (solo una vez, ~400 MB)
ollama pull embeddinggemma:latest
```

> El contenedor Docker se conecta a tu Ollama local a través de `host.docker.internal:11434`.
> En Linux puede ser necesario cambiar `EMBEDDING_BASE_URL=http://172.17.0.1:11434/v1` en el `.env`.

### 3 — Levantar con Docker (recomendado)

```bash
docker compose up --build

# En background
docker compose up --build -d

# Verificar que funciona
curl http://localhost:8000/health
```

La API queda disponible en:
- `http://localhost:8000` — API
- `http://localhost:8000/docs` — Swagger UI interactivo

### 3 — Alternativa sin Docker (solo desarrollo local)

```bash
uv sync
uv run uvicorn app.main:app --reload
```

---

## Variables de entorno

Copia `.env.example` a `.env` y rellena los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SUPABASE_URL` | URL del proyecto Supabase | `https://xxxx.supabase.co` |
| `SUPABASE_PUBLIC_KEY` | Clave anon/public de Supabase | `eyJ...` |
| `SUPABASE_SECRET_KEY` | Clave service_role de Supabase | `eyJ...` |
| `GROQ_API_KEY` | API key de Groq para el LLM | `gsk_...` |
| `GROQ_MODEL` | Modelo LLM para generación | `meta-llama/llama-4-scout-17b-16e-instruct` |
| `GROQ_JUDGE_MODEL` | Modelo para evaluaciones | `llama-3.3-70b-versatile` |
| `LLM_BASE_URL` | URL base del proveedor LLM | `https://api.groq.com/openai/v1` |
| `EMBEDDING_BASE_URL` | URL de Ollama para embeddings | `http://host.docker.internal:11434/v1` |
| `EMBEDDING_MODEL` | Modelo de embeddings | `embeddinggemma:latest` |
| `CHROMA_PATH` | Ruta a la base vectorial | `./chroma_db` |
| `CHROMA_COLLECTION` | Nombre de la colección | `documentos_fiscales` |

---

## Migraciones de base de datos

Aplicar en orden desde el **SQL Editor de Supabase**, uno por uno:

```
migrations/20260519140000_create_organizaciones.sql
migrations/20260519140001_create_roles.sql
migrations/20260519140002_create_categorias.sql
migrations/20260519140003_create_usuarios.sql
migrations/20260519140007_create_formas_pago.sql
migrations/20260519140008_create_documentos.sql
migrations/20260519140009_create_conversaciones.sql
migrations/20260519140010_create_extracciones.sql
migrations/20260519140011_rls_policies.sql
migrations/20260519140012_seed_data.sql
migrations/20260604230000_trigger_user.sql
```

---

## Ingesta de documentos

El sistema RAG lee PDFs y los indexa en ChromaDB con embeddings de Ollama.
Este paso es necesario una sola vez (o cuando agregues documentos nuevos).

### 1 — Colocar los PDFs en la carpeta `data/`

```
VISIR-Backend/
└── data/
    ├── guia_cfdi_4.pdf
    ├── regimenes_fiscales.pdf
    └── ...
```

### 2 — Ejecutar la ingesta

**Con uv (desarrollo local):**

```bash
uv run python -m ingestion.run              # ingestar todos los PDFs en data/
uv run python -m ingestion.run --stats      # ver estado actual de ChromaDB
uv run python -m ingestion.run --preview    # previsualizar chunks sin indexar
uv run python -m ingestion.run --reset      # limpiar ChromaDB y reingestar
```

**Con Docker (si el sistema ya está levantado):**

```bash
./scripts/ingestar.sh
./scripts/ingestar.sh --stats
./scripts/ingestar.sh --reset
```

**Vía endpoint HTTP:**

```bash
# Lanzar ingesta en background
curl -X POST http://localhost:8000/v1/ingest/run \
  -H "Authorization: Bearer <tu_jwt>"

# Ver estadísticas
curl http://localhost:8000/v1/ingest/stats \
  -H "Authorization: Bearer <tu_jwt>"
```

> La ingesta detecta automáticamente qué archivos ya están indexados
> y solo procesa los nuevos o modificados (deduplicación por hash SHA-256).

---

## Endpoints

### Autenticación

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/v1/auth/registro` | No | Registrar usuario con email y contraseña |
| `POST` | `/v1/auth/login` | No | Iniciar sesión, devuelve JWT |
| `POST` | `/v1/auth/logout` | ✅ JWT | Cerrar sesión |

**Ejemplo — login:**
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@empresa.com", "password": "contraseña123"}'
```

Respuesta:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### Documentos

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/v1/documentos` | ✅ JWT | Listar documentos del usuario |
| `POST` | `/v1/documentos/cargar` | ✅ JWT | Subir un documento |

---

### Asistente fiscal (RAG)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/v1/ia/preguntar` | ✅ JWT | Consulta RAG — recupera fragmentos y genera respuesta |
| `POST` | `/v1/ia/embeddings` | ✅ JWT | Vectorizar un texto con el modelo de embeddings |
| `POST` | `/v1/ia/embeddings/buscar` | ✅ JWT | Búsqueda semántica directa en ChromaDB (sin LLM) |

**Ejemplo — consulta RAG:**
```bash
curl -X POST http://localhost:8000/v1/ia/preguntar \
  -H "Authorization: Bearer <tu_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué RFC genérico se usa para facturar a extranjeros?", "top_k": 5}'
```

Respuesta:
```json
{
  "solicitud_id": "abc-123",
  "respuesta": "Para facturar a extranjeros sin RFC, se utiliza el RFC genérico XEXX010101000...",
  "tiene_cobertura": true,
  "fuentes_citadas": ["Anexo_20_Guia_Llenado_CFDI.pdf"],
  "chunks_recuperados": [...],
  "fuentes": ["Anexo_20_Guia_Llenado_CFDI.pdf"],
  "latencias_ms": {"recuperacion": 120.3, "generacion": 843.1},
  "tokens": {
    "tokens_entrada": 1842,
    "tokens_salida": 213
  }
}
```

> `tiene_cobertura: false` indica que ningún fragmento en ChromaDB cubre la pregunta.
> En ese caso la respuesta es siempre: `"El contexto disponible no cubre esta pregunta."`

---

### Ingesta

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/v1/ingest/run` | ✅ JWT | Lanzar pipeline de ingesta de PDFs |
| `GET` | `/v1/ingest/stats` | ✅ JWT | Estadísticas actuales de ChromaDB |

---

### Sistema

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/health` | No | Estado del sistema y disponibilidad del RAG |

Respuesta de `/health`:
```json
{
  "status": "ok",
  "version": "0.2.0",
  "rag_disponible": true
}
```

---

## Evaluación del RAG

El módulo `evaluaciones/` permite medir la calidad del sistema con un dataset de 30 preguntas fiscales.

### Modo recall (rápido, sin costo de LLM)

Mide Recall@1, @3 y @5: si los documentos correctos aparecen entre los primeros resultados recuperados. Ideal para correr en cada PR o antes de un despliegue.

```bash
uv run python -m evaluaciones.run_eval --modo recall
```

### Modo completo (con juez LLM)

Además del recall, evalúa **fidelidad** (¿el LLM inventó información?) y **relevancia** (¿la respuesta responde la pregunta?) usando un segundo modelo como juez. Para usar en sprint review.

```bash
uv run python -m evaluaciones.run_eval --modo completo
```

Los resultados se guardan en `validation_results/` como `.json` y `.md`.

---

## Comandos útiles

```bash
# ── Docker ───────────────────────────────────────────────────────────────────
make dev                          # levantar
make dev-down                     # bajar
make dev-logs                     # logs en tiempo real
make dev-reset                    # bajar + borrar volúmenes + reconstruir

# Sin make:
docker compose up --build -d
docker compose logs -f api
docker compose down
docker compose down -v            # ⚠️ borra ChromaDB y volúmenes

# ── Desarrollo local ──────────────────────────────────────────────────────────
uv sync                           # instalar / sincronizar dependencias
uv run uvicorn app.main:app --reload

# ── Calidad de código ─────────────────────────────────────────────────────────
uv run ruff check app --fix
uv run ruff format app
uv run mypy app
uv run pytest
uv run pre-commit run --all-files
```

---

## Estructura del proyecto

```
VISIR-Backend/
├── app/
│   ├── core/           # config, database, dependencies, logging
│   ├── routers/        # auth, documentos, ia, ingest
│   ├── services/       # auth_service, documents_service, rag_service
│   ├── repositories/   # auth_repository, documents_repository
│   ├── schemas/        # auth, documentos, consulta, ingest, user
│   └── main.py         # punto de entrada FastAPI
├── rag/
│   ├── chain.py        # cadena LangChain + validaciones Pydantic
│   ├── retriever.py    # recuperación semántica con reranking
│   ├── store.py        # wrapper ChromaDB
│   ├── embeddings.py   # cliente embeddings OpenAI-compatible
│   ├── config.py       # RAGConfig
│   └── hasher.py       # deduplicación por hash SHA-256
├── ingestion/
│   ├── run.py          # CLI: uv run python -m ingestion.run
│   ├── pipeline.py     # pipeline principal
│   ├── chunker.py      # chunking semántico
│   └── loader.py       # carga de PDFs y Markdown
├── evaluaciones/
│   ├── run_eval.py     # CLI de evaluación (recall / completo)
│   ├── juez.py         # cadenas LangChain para fidelidad y relevancia
│   ├── metricas.py     # cálculo de Recall@k
│   ├── reporte.py      # generador de reporte Markdown
│   ├── data/
│   │   └── eval_dataset.json   # 30 preguntas fiscales con respuesta esperada
│   └── prompts/        # plantillas para el juez LLM
├── migrations/         # SQL para Supabase en orden numérico
├── data/               # ← coloca aquí los PDFs a ingestar
├── chroma_db/          # base vectorial (generada por la ingesta, no versionar)
├── scripts/
│   ├── ingestar.sh     # atajo para ingesta vía Docker
│   └── pull_ollama_model.sh
├── tests/
├── docs/               # documentación técnica detallada
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Solución de problemas

**`uv: command not found`**
Instalar con el comando de la sección Requisitos y abrir una terminal nueva.

**Ollama no responde desde Docker**

En Mac/Windows funciona automáticamente con `host.docker.internal`. En Linux:
```bash
# Verificar la IP del host
docker compose exec api curl http://172.17.0.1:11434/api/tags

# Si responde, actualizar en .env:
# EMBEDDING_BASE_URL=http://172.17.0.1:11434/v1

# También asegurarse de que Ollama escucha en todas las interfaces
OLLAMA_HOST=0.0.0.0 ollama serve
```

**RAG devuelve 503 o `rag_disponible: false`**
El API arranca aunque Ollama no esté disponible. Verificar:
1. Que Ollama esté corriendo: `curl http://localhost:11434/api/tags`
2. Que el modelo esté descargado: `ollama list`
3. Que `EMBEDDING_BASE_URL` en `.env` apunte a Ollama correctamente

**El endpoint `/v1/ia/preguntar` devuelve "El contexto disponible no cubre esta pregunta."**
El RAG no encontró fragmentos relevantes. Verificar:
1. Que la ingesta se ejecutó correctamente: `uv run python -m ingestion.run --stats`
2. Que ChromaDB tiene chunks: el conteo debe ser mayor a 0
3. Que el volumen de Docker está montado correctamente (`./chroma_db:/app/chroma_db` en `docker-compose.yml`)

**Puerto 8000 ocupado**
```yaml
# docker-compose.yml — cambiar el puerto izquierdo
ports:
  - "8001:8000"
```

**Error de credenciales de Supabase**
Verificar que `SUPABASE_URL`, `SUPABASE_PUBLIC_KEY` y `SUPABASE_SECRET_KEY`
están copiados correctamente desde `Settings → API` en el dashboard de Supabase.

**Las migraciones fallan**
Aplicar en el orden numérico indicado, una por una desde el SQL Editor de Supabase.

**Pre-commit cancela el commit**
```bash
uv run ruff check app --fix
uv run pre-commit run --all-files
```

---

## Documentación técnica

| Archivo | Contenido |
|---|---|
| `docs/01_Arquitectura.md` | Capas del proyecto y flujo de peticiones |
| `docs/02_Configuracion.md` | Variables de entorno, ruff, mypy, pytest, pre-commit |
| `docs/03_Docker.md` | Dockerfile multi-stage y docker-compose |
| `docs/04_Endpoints.md` | Referencia completa de endpoints y ejemplos |
| `docs/ER.md` | Esquema de base de datos y diagrama ER |