# Visir API

Backend del sistema Visir — ERP inteligente con procesamiento de facturas XML (CFDI).

Construido con **FastAPI** + **Supabase** + **uv**.

---

## Requisitos

- [Python 3.12](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) — gestor de dependencias
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Verificar que están instalados:
```bash
python --version   # 3.12.x
uv --version
docker --version
```

Instalar uv si no lo tienes:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Arranque rápido

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Visir-Api

# 2. Copiar variables de entorno y rellenar credenciales
cp .env.example .env

# 3. Levantar con Docker
make dev
```

El servidor queda disponible en:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

Verificar que funciona:
```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

---

## Arranque sin Docker (solo Supabase cloud)

```bash
# 1. Instalar dependencias
uv sync

# 2. Rellenar .env con credenciales de Supabase
# SUPABASE_URL, SUPABASE_PUBLIC_KEY, SUPABASE_SECRET_KEY

# 3. Levantar el servidor
uv run uvicorn app.main:app --reload
```

> Si usas Supabase cloud, comenta los servicios `postgres` y `redis` en `docker-compose.yml`. Ver `docs/03_Docker.md`.

---

## Migraciones

Aplicar los archivos de `migrations/` **en orden numérico** desde el SQL Editor de Supabase:

```
20260519140000_create_organizaciones.sql
20260519140001_create_roles.sql
20260519140002_create_categorias.sql
20260519140003_create_usuarios.sql
20260519140004_create_emisores.sql
20260519140005_create_formas_pago.sql
20260519140006_create_documentos.sql
20260519140007_create_extracciones.sql
20260519140008_create_conversaciones.sql
20260519140009_rls_policies.sql
20260519140010_create_receptores.sql
20260519140011_seed_data.sql
```

---

## Comandos útiles

```bash
make dev            # levantar Docker
make dev-down       # bajar Docker
make dev-logs       # ver logs de la API
make dev-reset      # reset completo (borra volúmenes)

uv run ruff check app --fix    # linter
uv run mypy app                # tipos
uv run pytest                  # tests
uv run pre-commit run --all-files
```

---

## Estructura

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

| Documento | Contenido |
|---|---|
| `docs/01_Arquitectura.md` | Capas del proyecto y flujo de peticiones |
| `docs/02_Configuracion.md` | Variables de entorno, ruff, mypy, pytest, pre-commit |
| `docs/ER.md` | Esquema de base de datos y diagrama ER |
| `docs/03_Docker.md` | Dockerfile multi-stage y docker-compose |
| `docs/04_Endpoints.md` | Referencia completa de endpoints |

---

## Solución de problemas comunes

**Puerto 8000 ocupado**
```yaml
# En docker-compose.yml cambiar:
ports:
  - "8001:8000"   # usar el puerto libre que prefieras
```

**Error de credenciales de Supabase**
Verificar que `SUPABASE_URL`, `SUPABASE_PUBLIC_KEY` y `SUPABASE_SECRET_KEY` están correctamente copiados del dashboard de Supabase en `Settings > API`.

**`uv: command not found`**
Instalar uv con el comando de la sección Requisitos y reiniciar la terminal.

**La API arranca pero `/supabase` devuelve error**
- Verificar que las migraciones se aplicaron en Supabase.
- Verificar que el `.env` tiene las credenciales correctas.
- Revisar los logs: `make dev-logs`.

**`ModuleNotFoundError` al correr sin Docker**
```bash
uv sync   # instalar dependencias
```

**Pre-commit falla en el commit**
```bash
uv run pre-commit run --all-files   # ver qué falla
uv run ruff check app --fix         # corregir automáticamente
```
