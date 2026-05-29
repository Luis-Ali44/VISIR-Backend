# Arquitectura por capas

La API sigue una arquitectura de separación de responsabilidades en capas. Cada capa tiene una función específica y solo se comunica con la capa correspondinete, lo que hace que el código sea fácil de mantener y extender.

Se trabaja con FastAPI y el proveedor de base de datos y autenticación es Supabase.


## Estructura de carpetas

app/
├── routers/        # Capa HTTP — recibe y responde peticiones
├── services/       # Capa de negocio — lógica y reglas
├── repositories/   # Capa de datos — consultas a Supabase
├── schemas/        # Modelos Pydantic — validación de entrada/salida
└── core/           # Configuración global y cliente de Supabase



## Capas

### `routers/`
Recibe las peticiones HTTP, valida los datos de entrada con los schemas y delega al servicio correspondiente. No contiene lógica de negocio. Cada archivo agrupa los endpoints de un recurso.

### `services/`
Contiene la lógica de negocio. Orquesta las operaciones: valida reglas, llama a los repositorios y construye la respuesta final. Es la única capa que puede llamar a repositorios.

### `repositories/`
Único punto de contacto con la base de datos. Hace las consultas al cliente de Supabase y devuelve los datos crudos al servicio. No contiene lógica de negocio.

### `schemas/`
Define los modelos Pydantic para validar y serializar los datos que entran y salen de la API. Separados por recurso. Cada recurso puede tener un modelo de creación (`Create`), uno de respuesta (`Response`) y uno de actualización (`Update`) según lo necesite.

### `core/`
Configuración y utilidades compartidas por todas las capas:
- `config.py` — variables de entorno cargadas con Pydantic Settings
- `database.py` — instancia del cliente de Supabase

---

## Flujo de una petición

```
Cliente HTTP
    │
    ▼
routers/          → valida entrada con schema, llama al service
    │
    ▼
services/         → aplica lógica de negocio, llama al repository
    │
    ▼
repositories/     → consulta Supabase, devuelve datos
    │
    ▼
services/         → construye respuesta
    │
    ▼
routers/          → serializa con schema de respuesta, devuelve al cliente
```

---

## Convenciones

- Un archivo por recurso en cada capa (`documents_router.py`, `documents_service.py`, `documents_repository.py`, `documents_schema.py`).
- Los routers solo importan de services.
- Los services solo importan de repositories y schemas.
- Los repositories solo importan de `core/database.py`.
- Los schemas no importan de ninguna otra capa.
