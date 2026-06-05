# Visir API

Backend del sistema Visir — ERP inteligente 

FastAPI + Supabase + uv.

---

## Requisitos

Antes de empezar verifica que tienes instalado:

- [Python 3.12](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) — gestor de dependencias
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
python --version   # debe ser 3.12.x
uv --version
docker --version
```

Si no tienes uv, puedes intalarlo:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Arranque local

### Opción A — con Docker (recomendado)

```bash
# 1. clonar el repo
git clone https://github.com/Luis-Ali44/VISIR-Backend.git
cd Visir-Api

# 2. copiar variables de entorno y rellenar credenciales
cp .env.example .env

# 3. levantar
make dev

si no tienen make instalado pueden correr directemnte:
docker compose up --build
```

La API queda disponible en:
- `http://localhost:8000`
- `http://localhost:8000/docs` — Swagger UI

Verificar que funciona:
```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

### Opción B — sin Docker (solo Supabase)

```bash
# 1. instalar dependencias
uv sync

# 2. rellenar .env con credenciales de Supabase

# 3. levantar
uv run uvicorn app.main:app --reload
```
---

## Migraciones

Aplicar en orden desde el **SQL Editor de Supabase**, uno por uno:

```
20260519140000_create_organizaciones.sql
20260519140001_create_roles.sql
20260519140002_create_categorias.sql
20260519140003_create_usuarios.sql
20260519140007_create_formas_pago.sql
20260519140008_create_documentos.sql
20260519140009_create_conversaciones.sql
20260519140010_create_extracciones.sql
20260519140011_rls_policies.sql
20260519140012_seed_data.sql
```

---

## Comandos útiles

```bash
make dev            # levantar Docker
make dev-down       # bajar
make dev-logs       # ver logs de la API en tiempo real
make dev-reset      # reset completo — borra volúmenes y reconstruye

uv run ruff check app --fix   # linter
uv run mypy app               # tipos
uv run pytest                 # tests
uv run pre-commit run --all-files
```

---

## Estructura del proyecto

```
app/
├── routers/        # endpoints HTTP
├── services/       # lógica de negocio
├── repositories/   # acceso a Supabase
├── schemas/        # modelos Pydantic
└── core/           # config y cliente de Supabase
migrations/         # SQL en orden numérico
docs/               # documentación
tests/              # pruebas
```

---

## Documentación

| Archivo | Contenido |
|---|---|
| `docs/01_Arquitectura.md` | Capas del proyecto y flujo de peticiones |
| `docs/02_Configuracion.md` | Variables de entorno, ruff, mypy, pytest, pre-commit |
| `docs/ER.md` | Esquema de base de datos y diagrama ER |
| `docs/03_Docker.md` | Dockerfile multi-stage y docker-compose |
| `docs/04_Endpoints.md` | Referencia de endpoints y tests |

---

## Solución de problemas

**Puerto 8000 ocupado**
```yaml
# docker-compose.yml — cambiar el puerto izquierdo
ports:
  - "8001:8000"
```

**Error de credenciales de Supabase**
Verificar que `SUPABASE_URL`, `SUPABASE_PUBLIC_KEY` y `SUPABASE_SECRET_KEY` están correctamente copiados desde `Settings > API` en el dashboard de Supabase.

**`uv: command not found`**
Instalar uv con el comando de la sección Requisitos y abrir una terminal nueva.


**Docker no levanta — error en `depends_on`**
El compose espera que postgres y redis estén healthy. Si usas Supabase cloud, comentar esos servicios y el `depends_on` de `api`. Ver `docs/03_Docker.md`.

**La API arranca pero los endpoints fallan**
- Verificar que las migraciones se aplicaron en Supabase en el orden correcto.
- Revisar logs: `make dev-logs`.

**Pre-commit cancela el commit**
```bash
uv run ruff check app --fix   # corregir automáticamente
uv run pre-commit run --all-files
```
