# Configuración del proyecto

---

## Variables de entorno

Las variables sensibles se guardan en `.env` y se cargan con Pydantic Settings desde `app/core/config.py`.Existe el  `.env.example` como plantilla para no subir el `.env`

```dotenv

# app
APP_NAME="visir_app"
APP_VERSION="0.1.0"
ENVIRONMENT="development"

# servidor
HOST=0.0.0.0
PORT=8000

# supabase
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_PUBLIC_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...

# postgres local (solo si no usas Supabase cloud)
DATABASE_URL=postgresql://visir:visir123@localhost:5432/visir_dev

# redis
REDIS_URL=redis://localhost:6379
```

```bash
cp .env.example .env
# rellenar credenciales
```

---

## Gestión de dependencias — uv

Las dependencias se definen en `pyproject.toml` y se resuelven con uv. El archivo `uv.lock` fija las versiones exactas para que todos los entornos sean idénticos.

```bash
uv sync           # instala todo 
uv sync --no-dev  # solo producción 
uv add <paquete>
uv remove <paquete>
```

### Producción
| Paquete | Uso |
|---|---|
| `fastapi` | Framework HTTP |
| `uvicorn` | Servidor ASGI |
| `pydantic` | Validación de datos |
| `pydantic-settings` | Carga de variables de entorno |
| `supabase` | Cliente de Supabase |
| `python-multipart` | Parseo de `multipart/form-data` para subida de archivos |
| `email-validator` | Validación de emails en schemas Pydantic |

### Desarrollo
| Paquete | Uso |
|---|---|
| `ruff` | Linter y formateador |
| `mypy` | Verificación de tipos |
| `pytest` | Testing |
| `httpx` | Cliente HTTP para tests |
| `pre-commit` | Hooks antes del commit |

---

## Ruff

Configurado en `pyproject.toml` bajo `[tool.ruff]`.

```bash
uv run ruff check app          # revisar
uv run ruff check app --fix    # corregir automáticamente
uv run ruff format app         # formatear
```

| Prefijo | Qué revisa |
|---|---|
| `E` / `W` | Estilo PEP 8 |
| `F` | Variables no usadas, imports sobrantes |
| `I` | Orden de imports |
| `N` | Nombres de clases y funciones |
| `UP` | Sintaxis moderna de Python |
| `B` | Bugs comunes |
| `C4` | Comprehensions más limpias |
| `SIM` | Simplificación de código |
| `ASYNC` | Reglas para código async |
| `RUF` | Reglas propias de Ruff |

Excepciones: `B008` ignorado globalmente (FastAPI usa llamadas a función en `Depends()`). `S101` permitido en `tests/`.

---

## Mypy

```bash
uv run mypy app
```

| Opción | Efecto |
|---|---|
| `disallow_untyped_defs` | Todas las funciones deben tener tipos |
| `warn_return_any` | Avisa si se retorna `Any` |
| `warn_unused_ignores` | Avisa si un `# type: ignore` ya no es necesario |
| `ignore_missing_imports` | No falla si una librería no tiene stubs |
| `plugins = ["pydantic.mypy"]` | Soporte para modelos Pydantic |

Los tests tienen `disallow_untyped_defs = false`.

---

## Pytest

```bash
uv run pytest                   # todos los tests
uv run pytest tests/test_x.py   # un archivo
uv run pytest -v                # muestra mas detalles 
```

Los tests viven en `tests/`. Ver `docs/04_Endpoints.md` para los casos de prueba de cada endpoint.

---

## Pre-commit

```bash
uv run pre-commit install             # activar
uv run pre-commit run --all-files     # correr manualmente
```

Hooks configurados en `.pre-commit-config.yaml`:
1. **ruff** — linting con auto-fix
2. **ruff-format** — formateo
3. **mypy** — verificación de tipos

Si algún hook falla, el commit se cancela hasta que se corrija.
