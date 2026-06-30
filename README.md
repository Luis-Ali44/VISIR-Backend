# VISIR API

Backend del sistema VISIR — ERP inteligente con asistente fiscal RAG y
extracción automática de CFDIs (PDF, imagen y XML).

**Stack:** FastAPI · Supabase · ChromaDB · Ollama · LangChain / LangGraph · PaddleOCR · Mistral · uv

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
# Editar .env con tus credenciales de Supabase, Groq y Mistral
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

### Alternativa sin Docker (solo desarrollo local)

```bash
uv sync
uv run uvicorn app.main:app --reload
```

> **Nota:** la primera vez que `uv sync` instale PaddleOCR/PaddlePaddle puede tardar varios
> minutos por el tamaño de los paquetes. Si vienes de una instalación manual previa con
> pip (entorno solo para el módulo de extracción), revisa que no tengas dos entornos
> virtuales distintos activos a la vez.

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
| `LLM_API_KEY` | API key del proveedor LLM (p. ej. Groq) | `gsk_...` |
| `LLM_MODEL` | Modelo LLM para generación y enrutamiento | `llama-3.3-70b-versatile` |
| `LLM_BASE_URL` | URL base del proveedor LLM | `https://api.groq.com/openai/v1` |
| `LLM_TEMPERATURE` | Temperatura de generación del LLM | `0.2` |
| `LLM_MAX_TOKENS` | Máximo de tokens de salida del LLM | `1024` |
| `EMBEDDING_BASE_URL` | URL de Ollama para embeddings | `http://host.docker.internal:11434/v1` |
| `EMBEDDING_MODEL` | Modelo de embeddings | `embeddinggemma:latest` |
| `CHROMA_PATH` | Ruta a la base vectorial | `./chroma_db` |
| `CHROMA_COLLECTION` | Colección de normativa SAT (compartida, solo lectura) | `documentos_fiscales` |
| `CHROMA_ORG_COLLECTION` | Colección de documentos/CFDIs por organización | `documentos_organizacion` |
| `MISTRAL_API_KEY` | API key de Mistral, usada por el extractor de CFDIs | `tu_clave_aqui` |

> `CHROMA_COLLECTION` y `CHROMA_ORG_COLLECTION` son colecciones **separadas** dentro del
> mismo ChromaDB: la primera es normativa SAT compartida entre todas las organizaciones
> (solo se llena vía la ingesta administrativa, ver más abajo); la segunda es donde
> caen los CFDIs y documentos que cada organización sube, aislados entre sí por un
> filtro obligatorio de metadata `id_organizacion` en cada consulta.

---

## Migraciones de base de datos

Aplicar en orden desde el **SQL Editor de Supabase**, uno por uno:

```
migrations/20260519140000_create_organizaciones.sql
migrations/20260519140001_create_roles.sql
migrations/20260519140002_create_categorias.sql
migrations/20260519140003_create_usuarios.sql
migrations/20260519140005_create_categorias.sql
migrations/20260519140007_create_formas_pago.sql
migrations/20260519140008_create_documentos.sql
migrations/20260519140009_create_conversaciones.sql
migrations/20260519140010_create_extracciones.sql
migrations/20260519140011_rls_policies.sql
migrations/20260519140012_seed_data.sql
migrations/20260604230000_trigger_user.sql
migrations/20260610100001_create_tipos_comprobantes.sql
```

---

## Flujo general del sistema

```
                    ┌─────────────────────────────────────┐
                    │   POST /v1/documentos/cargar         │
                    │   (PDF, imagen o XML)                │
                    └──────────────┬────────────────────────┘
                                   │
                 1. Guarda archivo en Storage + metadata en `documentos`
                                   │
                 2. Extrae el CFDI (OCR+Mistral para PDF/imagen,
                    parseo directo para XML) → guarda en `extracciones`
                                   │
                 3. En background: genera embeddings del CFDI y los
                    indexa en la colección de organización (Chroma),
                    aislados por id_organizacion
                                   │
                    ┌──────────────▼────────────────────────┐
                    │   POST /v1/consultas/preguntar         │
                    │   (pregunta en lenguaje natural)        │
                    └──────────────┬────────────────────────┘
                                   │
                 Enrutador léxico + LLM clasifica la pregunta en:
                   - NORMATIVA     → recupera de documentos_fiscales (SAT)
                   - CFDI_PROPIOS  → recupera de `extracciones` (SQL) +
                                      documentos_organizacion (Chroma)
                   - HIBRIDO       → ambas fuentes, en paralelo
                                   │
                          Respuesta generada por el LLM
```

### Extracción de CFDIs (OCR + LLM + parser XML)

El módulo `app/services/Extraccion/` procesa cualquier archivo subido vía
`/v1/documentos/cargar` y, si reconoce un CFDI, lo estructura y valida:

```
PDF/Imagen → ocr_preprocess (clasifica página) → ocr_paddle (extrae texto)
           → pipeline (detecta versión/UUID) → Mistral (estructura JSON)
           → schema_extraccion (valida Pydantic) → fila en `extracciones`

XML        → xml_parser → schema_extraccion (valida Pydantic) → fila en `extracciones`
```

Si el archivo subido no es un CFDI reconocible (p. ej. un PDF normativo o una
imagen no fiscal), el documento se guarda normalmente y la extracción simplemente
se omite — no se considera un error.

Requiere una API key de [Mistral AI](https://console.mistral.ai/) configurada en
`MISTRAL_API_KEY`.

---

## Ingesta de normativa SAT al RAG general

El sistema RAG lee PDFs normativos del SAT y los indexa en la colección
compartida `documentos_fiscales` con embeddings de Ollama. Este paso es
administrativo, manual, y necesario una sola vez (o cuando agregues
documentos normativos nuevos) — es independiente de la ingesta automática
de CFDIs por organización, que ocurre sola al subir un documento.

### 1 — Colocar los PDFs en la carpeta `data/`

```
VISIR-Backend/
└── data/
    ├── Anexo_20_Guia_Llenado_CFDI_v4_v2.pdf
    ├── RMF_2026_Completa_limpio.pdf
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
| `POST` | `/v1/documentos/cargar` | ✅ JWT | Subir un documento (PDF, imagen o XML). Extrae el CFDI si aplica e ingesta al RAG de organización en background. |
| `POST` | `/v1/documentos/lote` | ✅ JWT | Subir varios documentos a la vez |
| `GET` | `/v1/documentos` | ✅ JWT | Listar todos los documentos (paginado) |
| `GET` | `/v1/documentos/MyDocuments` | ✅ JWT | Listar documentos del usuario autenticado en su organización |
| `GET` | `/v1/documentos/{document_id}` | ✅ JWT | Obtener un documento por ID |

---

### Extracciones (CFDIs procesados)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/v1/Extracciones` | ✅ JWT | Listar extracciones de la organización del usuario autenticado (paginado) |
| `GET` | `/v1/Extracciones/{extraccion_id}` | ✅ JWT | Obtener una extracción por ID, solo si pertenece a la organización del usuario |

---

### Asistente fiscal (RAG)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/v1/consultas/preguntar` | ✅ JWT | Consulta RAG — clasifica la pregunta (normativa / CFDIs propios / híbrida), recupera contexto y genera respuesta |

**Ejemplo — consulta normativa:**
```bash
curl -X POST http://localhost:8000/v1/consultas/preguntar \
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
  "fuentes_citadas": ["sat", "rfc"],
  "latencias_ms": {"grafo_total": 843.1}
}
```

**Ejemplo — consulta sobre facturas propias:**
```bash
curl -X POST http://localhost:8000/v1/consultas/preguntar \
  -H "Authorization: Bearer <tu_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuánto gasté el mes pasado en total?", "top_k": 5}'
```

---

### Ingesta (normativa SAT)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/v1/ingest/run` | ✅ JWT | Lanzar pipeline de ingesta de PDFs normativos |
| `GET` | `/v1/ingest/stats` | ✅ JWT | Estadísticas actuales de ChromaDB (colección de normativa) |

---

### Sistema

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/health` | No | Estado del sistema |
| `GET` | `/` | No | Mensaje de bienvenida |

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
│   ├── core/                  # config, database, dependencies, logging
│   ├── routers/                # auth, documentos, extracciones, ia, ingest
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── documents_service.py
│   │   ├── extracciones_service.py
│   │   ├── rag_service.py         # grafo LangGraph del asistente fiscal
│   │   ├── org_ingestion_service.py  # ingesta CFDIs/documentos → RAG de organización
│   │   └── Extraccion/             # OCR + Mistral + parser XML de CFDIs
│   ├── repositories/           # documents, extracciones, auth
│   ├── schemas/                # auth, documentos, extraccion, consulta, ingest, user
│   └── main.py                 # punto de entrada FastAPI
├── rag/
│   ├── chain.py                # cadena LangChain + validaciones Pydantic
│   ├── retriever.py             # FiscalRAGRetriever (normativa) + OrgRAGRetriever (organización)
│   ├── store.py                 # wrapper ChromaDB
│   ├── embeddings.py            # cliente embeddings OpenAI-compatible
│   ├── config.py                # RAGConfig (colección de normativa Y de organización)
│   └── hasher.py                # deduplicación por hash SHA-256
├── ingestion/
│   ├── run.py                   # CLI: uv run python -m ingestion.run
│   ├── pipeline.py               # pipeline principal (normativa SAT y organización)
│   ├── chunker.py                # chunking semántico
│   └── loader.py                 # carga de PDFs y Markdown
├── evaluaciones/                 # evaluación del RAG (recall, fidelidad, relevancia)
├── migrations/                   # SQL para Supabase en orden numérico
├── data/                         # ← coloca aquí los PDFs normativos a ingestar
├── chroma_db/                    # base vectorial (generada por la ingesta, no versionar)
├── scripts/
├── tests/
├── docs/                         # documentación técnica detallada
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

**`/v1/consultas/preguntar` devuelve 500 "RAGService no inicializado"**
El `lifespan` de `app/main.py` no construyó `app.state.rag_service`. Verificar:
1. Que solo exista UNA función `lifespan` en `app/main.py` (si hay dos definiciones
   con el mismo nombre, la segunda pisa silenciosamente a la primera sin error).
2. Que `LLM_API_KEY`, `LLM_BASE_URL` y `LLM_MODEL` estén configurados en `.env`.
3. Los logs de arranque del contenedor/proceso por si `FiscalRAGRetriever` o
   `FiscalRAGChain` lanzaron una excepción durante la inicialización.

**El endpoint de consultas responde pero no cita ningún documento**
1. Que la ingesta de normativa se ejecutó correctamente: `uv run python -m ingestion.run --stats`.
2. Que ChromaDB tiene chunks en la colección `documentos_fiscales`: el conteo debe ser mayor a 0.
3. Para preguntas sobre facturas propias, que el documento ya se haya subido y
   procesado vía `/v1/documentos/cargar` (revisar `GET /v1/Extracciones` para confirmar
   que la extracción se guardó).

**MISTRAL_API_KEY no configurada (al subir un PDF/imagen)**
La extracción de CFDIs vía OCR necesita una API key de Mistral. Configúrala en `.env`:
```bash
MISTRAL_API_KEY=tu_clave_aqui
```
Si el archivo es XML, no se necesita Mistral — el parseo es directo.

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
