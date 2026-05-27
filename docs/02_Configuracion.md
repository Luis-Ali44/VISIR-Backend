# Configuración del proyecto

---

## Variables de entorno

Las variables sensibles (URLs, credenciales) se guardan en `.env` y se cargan con **Pydantic Settings** desde `app/core/config.py`. Nunca se sube el `.env` al repositorio — existe un `.env.example` como plantilla.

```dotenv
# App
APP_NAME="visir_app"
APP_VERSION="0.1.0"
ENVIRONMENT="development"

# Servidor
HOST=0.0.0.0
PORT=8000

# Supabase
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_PUBLIC_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...

# Postgres local (solo si no usas Supabase cloud)
DATABASE_URL=postgresql://visir:visir123@localhost:5432/visir_dev

# Redis
REDIS_URL=redis://localhost:6379
```

Copiar el ejemplo y rellenar:
```bash
cp .env.example .env
```

---

## Gestión de dependencias — `uv`

Las dependencias se definen en `pyproject.toml` y se resuelven con **uv**. El archivo `uv.lock` fija las versiones exactas para que todos los entornos sean idénticos.

```bash
uv sync          # instala dependencias de producción y desarrollo
uv sync --no-dev # solo producción (usado en Docker)
uv add <paquete> # agregar una dependencia
uv remove <paquete>
```

### Dependencias de producción
| Paquete | Uso |
|---|---|
| `fastapi` | Framework HTTP |
| `uvicorn` | Servidor ASGI |
| `pydantic` | Validación de datos |
| `pydantic-settings` | Carga de variables de entorno |
| `supabase` | Cliente de Supabase |

### Dependencias de desarrollo
| Paquete | Uso |
|---|---|
| `ruff` | Linter y formateador |
| `mypy` | Verificación de tipos |
| `pytest` | Testing |
| `httpx` | Cliente HTTP para tests |
| `pre-commit` | Hooks antes del commit |

---

## Ruff — linter y formateador

Configurado en `pyproject.toml` bajo `[tool.ruff]`.

```bash
uv run ruff check app          # revisar errores
uv run ruff check app --fix    # corregir automáticamente
uv run ruff format app         # formatear
```

### Reglas activas
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
| `ASYNC` | Reglas para código async (relevante en FastAPI) |
| `RUF` | Reglas propias de Ruff |

### Excepciones
- `B008` — ignorado globalmente porque FastAPI usa llamadas a función en `Depends()`.
- `S101` — asserts permitidos dentro de `tests/`.

---

## Mypy — verificación de tipos

Configurado en `pyproject.toml` bajo `[tool.mypy]`.

```bash
uv run mypy app
```

### Opciones activas
| Opción | Efecto |
|---|---|
| `disallow_untyped_defs` | Todas las funciones deben tener tipos |
| `warn_return_any` | Avisa si se retorna `Any` |
| `warn_unused_ignores` | Avisa si un `# type: ignore` ya no es necesario |
| `ignore_missing_imports` | No falla si una librería no tiene stubs |
| `plugins = ["pydantic.mypy"]` | Soporte para modelos Pydantic |

Los tests tienen `disallow_untyped_defs = false` para no obligar tipos en fixtures y helpers de prueba.

---

## Pytest — testing

Configurado en `pyproject.toml` bajo `[tool.pytest.ini_options]`.

```bash
uv run pytest                  # correr todos los tests
uv run pytest tests/test_x.py  # correr un archivo específico
uv run pytest -v               # verbose
```

Los tests viven en `tests/`. Ver `docs/05_Endpoints.md` para los casos de prueba de cada endpoint.

---

## Pre-commit — hooks automáticos

Configurado en `.pre-commit-config.yaml`. Se ejecuta automáticamente antes de cada `git commit`.

```bash
uv run pre-commit install              # activar hooks (solo una vez)
uv run pre-commit run --all-files      # correr manualmente sobre todo
```

### Hooks configurados
1. **ruff** — linting con auto-fix
2. **ruff-format** — formateo
3. **mypy** — verificación de tipos

Si algún hook falla, el commit se cancela hasta que se corrija.
