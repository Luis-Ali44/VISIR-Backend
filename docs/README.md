# Visir API

Backend del Visir 

## Requisitos

- Python 3.12
- uv — instalar 
- Docker Desktop 

Verificar que están instalados:
```
python --version
uv --version
docker --version
```



## Levantar en local

```
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Visir-Api

# 2. Instalar dependencias
uv sync

# 3. Levantar el servidor
uv run uvicorn app.main:app --reload
```

El servidor queda disponible en `http://localhost:8000`

Verificar que funciona:

```powershell
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

---

## Comandos útiles

```powershell
uv run ruff check app              # linter
uv run mypy app                    # tipos
uv run pytest                      # tests
uv run pre-commit run --all-files  # verificar todo
```

---

## Docker

```powershell
docker build -t visir-api .
docker run --rm -p 8000:8000 visir-api
```

---

## Estructura

```
app/
├── routers/       # endpoints HTTP
├── services/      # lógica de negocio
├── repositories/  # acceso a datos
├── schemas/       # modelos Pydantic
└── core/          # configuración y utilidades
```