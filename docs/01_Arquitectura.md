# Arquitectura por capas

Visir API usa FastAPI con separación de responsabilidades en capas. Cada capa tiene una función específica y solo se comunica con la correspondiennte.

El proveedor de base de datos es Supabase. La autenticación la manejará Supabase Auth directamente.

---

## Estructura de carpetas

```
app/
├── routers/        # capa HTTP — recibe y responde peticiones
├── services/       # capa de negocio — lógica y reglas
├── repositories/   # capa de datos — consultas a Supabase
├── schemas/        # modelos Pydantic — validación de entrada/salida
└── core/           # configuración global y cliente de Supabase
```

---

## Capas

### `routers/`
Recibe las peticiones HTTP, valida los datos de entrada con los schemas y delega al servicio correspondiente. No contiene lógica de negocio. Cada archivo agrupa los endpoints de un recurso.

### `services/`
Contiene la lógica de negocio. Organiza las operaciones: valida reglas, llama a los repositorios y construye la respuesta. Es la única capa que puede llamar a repositorios.

### `repositories/`
Único punto de contacto con Supabase. Hace las consultas y devuelve los datos crudos al servicio. No contiene lógica de negocio.

### `schemas/`
Modelos Pydantic para validar y serializar los datos que entran y salen de la API. Separados por recurso. Cada recurso puede tener `Create` y `Response` según lo necesite.

### core — Configuración y utilidades compartidas:
- `config.py` — variables de entorno con Pydantic Settings
- `database.py` — instancia del cliente de Supabase
