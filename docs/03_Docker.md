# Docker

---

## Dockerfile

El Dockerfile usa **multi-stage build** para mantener la imagen de producción lo más pequeña posible.

```
Stage 1 (builder)  → instala dependencias con uv
Stage 2 (runtime)  → copia solo el .venv y el código, sin herramientas de build
```

### Etapas

**builder** — instala dependencias
```dockerfile
FROM python:3.12-slim AS builder
# Copia uv desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev --no-cache
```

**runtime** — imagen final limpia
```dockerfile
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

> En producción quitar `--reload` del CMD. Solo se usa en desarrollo.

---

## docker-compose.yml

El compose levanta tres servicios:

| Servicio | Imagen | Puerto | Uso |
|---|---|---|---|
| `api` | build local | `8000` | FastAPI |
| `postgres` | `postgres:16-alpine` | `5432` | Base de datos local |
| `redis` | `redis:7-alpine` | `6379` | Cache / colas (futuro) |

`api` espera a que `postgres` y `redis` estén healthy antes de arrancar (`depends_on` con `condition: service_healthy`).

---

## Comandos

Todos los comandos de Docker están en el `Makefile`:

```bash
make dev          # construir y levantar todos los servicios
make dev-down     # bajar los servicios
make dev-logs     # ver logs de la API en tiempo real
make dev-reset    # bajar, borrar volúmenes y volver a construir
```

O directamente con Docker:

```bash
docker compose up --build       # levantar
docker compose down             # bajar
docker compose down -v          # bajar y borrar volúmenes (reset de DB)
docker compose logs -f api      # logs en vivo
```

---

## Trabajar con Supabase cloud (sin postgres local)

Si usas Supabase cloud en lugar de postgres local, comenta o elimina los servicios `postgres` y `redis` del `docker-compose.yml` y asegúrate de que el `.env` tenga las credenciales de Supabase correctas.

```yaml
# Comentar estos servicios si usas Supabase cloud:
# postgres:
#   ...
# redis:
#   ...
```

Y en `api`, quitar el `depends_on`:
```yaml
api:
  build: .
  ports:
    - "8000:8000"
  env_file:
    - .env
  volumes:
    - ./app:/app/app
```

---

## Variables de entorno en Docker

El compose carga el `.env` automáticamente con `env_file: .env`. Asegúrate de que el archivo exista antes de correr `make dev`.

```bash
cp .env.example .env
# Rellenar credenciales
make dev
```

---

## Volúmenes

| Volumen | Qué guarda |
|---|---|
| `postgres_data` | Datos de PostgreSQL entre reinicios |
| `redis_data` | Datos de Redis entre reinicios |

`make dev-reset` borra estos volúmenes — útil para empezar desde cero en desarrollo.
