# Docker

---

## Dockerfile multi-stage

La imagen actual usa una construcción en dos etapas para mantener el contenedor de ejecución más pequeño y compatible con OCR/ML.

- Etapa 1: `builder` instala dependencias con `uv` y las librerías del sistema necesarias para `opencv`/`paddlepaddle`.
- Etapa 2: `runtime` copia el entorno virtual generado, la aplicación y los recursos adicionales (`resources`, `rag`, `ingestion`).

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:/opt/conda/bin:$PATH" \
    PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
ENV PYTHONPATH=/app
WORKDIR /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

> El Dockerfile real también instala `libgl1`, `libglib2.0-0`, `libgomp1`, y Miniconda para soportar partes del pipeline de extracción y evaluación.

---

## docker-compose.yml

El stack de desarrollo actual define cuatro servicios principales:

| Servicio | Imagen / build | Puerto | Uso |
|---|---|---|---|
| `api` | build local | `8000` | FastAPI principal |
| `worker` | build local | sin expuesto | worker de Celery para procesamiento de documentos |
| `postgres` | `postgres:16-alpine` | `5435` | Base de datos local de desarrollo |
| `redis` | `redis:7-alpine` | `6380` | Broker/cola para Celery |

`api` espera a que `postgres` y `redis` estén healthy antes de arrancar. El servicio `worker` depende de `redis` y de `api`.

---

## Comandos útiles

```bash
make dev          # construir y levantar la API
make dev-down     # bajar los servicios
make dev-logs     # ver logs de la API en tiempo real
make dev-reset    # bajar, borrar volúmenes y reconstruir todo
```

O directamente:

```bash
docker compose up --build
docker compose down
docker compose down -v
docker compose logs -f api
docker compose logs -f worker
```

---

## Supabase cloud y servicios locales

La configuración actual sigue usando Supabase para la base de datos y storage, mientras que `postgres` y `redis` son servicios locales para desarrollo. Si prefieres trabajar solo contra Supabase cloud, puedes dejar fuera los servicios locales y asegurar que el archivo `.env` tenga las credenciales correctas de Supabase.
---

## Volúmenes

| Volumen | Qué guarda |
|---|---|
| `postgres_data` | Datos persistentes de PostgreSQL |
| `redis_data` | Datos persistentes de Redis |
| `chroma_db` | Índice y base vectorial de ChromaDB |

`make dev-reset` elimina los volúmenes de PostgreSQL y Redis, útil cuando se quiere reiniciar el entorno desde cero.
