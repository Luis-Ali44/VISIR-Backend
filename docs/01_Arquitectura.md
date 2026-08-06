# Arquitectura por capas

Visir API usa FastAPI con separación de responsabilidades en capas. Cada capa tiene una función específica y solo se comunica con la correspondiente.

El sistema combina Supabase para autenticación y almacenamiento, ChromaDB para recuperación vectorial, Celery para procesamiento asíncrono y un pipeline RAG para consultas sobre normativa y CFDIs.

---

## Estructura de carpetas

```text
app/
├── core/           # configuración global, dependencias y utilidades compartidas
├── routers/        # endpoints HTTP y montaje de routers
├── services/       # lógica de negocio, RAG, extracción y tareas
├── repositories/   # acceso a Supabase y lógica de persistencia
├── schemas/        # modelos Pydantic para validación y respuesta
├── tasks/          # integración con Celery
└── main.py         # aplicación FastAPI y registro de routers
```

Además del backend, el proyecto incluye:

```text
rag/                # pipeline RAG y retrievers
ingestion/          # ingesta de normativa SAT a ChromaDB
evaluaciones/      # scripts de evaluación y métricas
supabase/migrations/ # migraciones SQL del modelo de datos
```

---

## Capas

### `routers/`
Recibe las peticiones HTTP, valida el input en la medida que corresponde al router y delega al servicio correspondiente. No debería contener lógica de negocio compleja.

### `services/`
Contiene la lógica de negocio: procesamiento de documentos, extracción de CFDIs, RAG, ingesta y tareas asíncronas.

### `repositories/`
Es el punto de contacto con Supabase y con la capa de datos. Agrupa las consultas y operaciones de persistencia.

### `schemas/`
Modelos Pydantic que definen la entrada/salida de la API y las estructuras de respuesta.

### `core/`
Contiene configuración global, dependencias de autenticación y utilidades compartidas.

---

## Flujo principal

1. El cliente sube un archivo por `POST /v1/documentos/cargar`.
2. El backend guarda el archivo y crea metadata en Supabase.
3. Un worker de Celery procesa el documento de forma asíncrona.
4. Se extrae su estructura y se guarda en `extracciones`.
5. Las consultas de IA se resuelven con un pipeline RAG que combina normativa SAT y CFDIs propios.
