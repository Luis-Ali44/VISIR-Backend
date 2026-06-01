# Docker

---

## Dockerfile multi-stage

Dos etapas para mantener la imagen de producción pequeña y sin herramientas de build.

**Stage 1 — builder**: instala dependencias con uv
**Stage 2 — runtime**: copia solo el `.venv` y el código

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev --no-cache

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yml

| Servicio | Imagen | Puerto | Uso |
|---|---|---|---|
| `api` | build local | `8000` | FastAPI |
| `postgres` | `postgres:16-alpine` | `5432` | Base de datos local |
| `redis` | `redis:7-alpine` | `6379` | Cache / colas |

`api` espera a que `postgres` y `redis` estén healthy antes de arrancar.

---

## Comandos

```bash
make dev          # construir y levantar
make dev-down     # bajar
make dev-logs     # logs de la API en tiempo real
make dev-reset    # bajar, borrar volúmenes y reconstruir
```

O directamente:

```bash
docker compose up --build
docker compose down
docker compose down -v     
docker compose logs -f api
```

---

## Usar Supabase cloud (sin postgres local)

Comentar los servicios `postgres` y `redis` en `docker-compose.yml` y quitar el `depends_on` de `api`:

```yaml
api:
  build: .
  ports:
    - "8000:8000"
  env_file:
    - .env
  volumes:
    - ./app:/app/app

# postgres:
#   ...
# redis:
#   ...
```

---

## Volúmenes

| Volumen | Qué guarda |
|---|---|
| `postgres_data` | Datos de PostgreSQL entre reinicios |
| `redis_data` | Datos de Redis entre reinicios |

`make dev-reset` borra estos volúmenes — útil para empezar desde cero.
