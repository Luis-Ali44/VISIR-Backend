# Etapa 1: Construcción (Builder)
FROM python:3.12-slim AS builder

# Copiar el binario oficial de uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar archivos de configuración (se recomienda incluir uv.lock si existe)
COPY pyproject.toml uv.lock* ./

# Instalar dependencias bloqueadas y sin entornos de desarrollo
RUN uv sync --frozen --no-dev --no-cache

# Etapa 2: Ejecución (Runtime)
FROM python:3.12-slim AS runtime

# Configuraciones de entorno para Python y PATH
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

ENV PYTHONPATH=/app

WORKDIR /app

# Corregido: 'builder' en minúsculas para coincidir con la etapa 1
COPY --from=builder /app/.venv /app/.venv
COPY app ./app
COPY rag ./rag
COPY ingestion ./ingestion
EXPOSE 8000

# Comando para iniciar FastAPI/Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
