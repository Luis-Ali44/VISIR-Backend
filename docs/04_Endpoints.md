# Endpoints

Base URL: `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

---

## General

### `GET /health`
Verifica que el servidor está corriendo.

**Respuesta `200`**
```json
{ "status": "ok", "version": "0.1.0" }
```

---

### `GET /supabase`
Prueba de conexión — devuelve todas las organizaciones.

**Respuesta `200`**
```json
[
  {
    "id": "11111111-1111-1111-1111-111111111111",
    "nombre": "Empresa Alpha",
    "descripcion": "Organización de prueba A",
    "created_at": "2026-05-19T14:00:00",
    "updated_at": "2026-05-19T14:00:00"
  }
]
```

---

## Documentos — `/v1/documentos`

### `POST /v1/documentos/cargar`
Sube un archivo al storage de Supabase y guarda sus metadatos en la tabla `documentos`.

**Request** — `multipart/form-data`
| Campo | Tipo |
|---|---|
| `file` | archivo |

**Tipos permitidos**: `application/pdf`, `text/xml`, `application/xml`
**Tamaño máximo**: 5 MB

**Respuesta `200`**
```json
{
  "id": "uuid",
  "nombre": "factura.pdf",
  "tipo": "application/pdf",
  "tamaño": 102400,
  "link": "documentos/uuid.pdf",
  "id_usuario": null,
  "id_organizacion": null,
  "created_at": "2026-05-19T14:00:00"
}
```

**Errores**
| Código | Motivo |
|---|---|
| `400` | Tipo de archivo no permitido |
| `400` | Archivo mayor a 5 MB |
| `400` | `content-type` nulo |

---

### `GET /v1/documentos`
Lista documentos con paginación por cursor.

**Query params**
| Param | Tipo | Default | Rango |
|---|---|---|---|
| `limit` | int | `10` | 1–50 |
| `cursor` | string | `null` | valor de `created_at` del último elemento recibido |

**Respuesta `200`**
```json
{
  "data": [
    {
      "id": "uuid",
      "nombre": "factura.pdf",
      "tipo": "application/pdf",
      "tamaño": 102400,
      "link": "documentos/uuid.pdf",
      "id_usuario": "uuid",
      "id_organizacion": "uuid",
      "created_at": "2026-05-19T14:00:00"
    }
  ],
  "next_cursor": "2026-05-19T14:00:00"
}
```

Cuando `next_cursor` es `null` no hay más páginas.

**Errores**
| Código | Motivo |
|---|---|
| `422` | `limit` fuera de rango|

---

### `GET /v1/documentos/id`
Obtiene un documento por su ID.

**Query params**
| Param | Tipo |
|---|---|
| `document_id` | string (UUID) |

**Respuesta `200`**
```json
[
  {
    "id": "uuid",
    "nombre": "factura.pdf",
    "tipo": "application/pdf",
    "tamaño": 102400,
    "link": "documentos/uuid.pdf",
    "id_usuario": "uuid",
    "id_organizacion": "uuid",
    "created_at": "2026-05-19T14:00:00"
  }
]
```

**Errores**
| Código | Motivo |
|---|---|
| `404` | Documento no encontrado |

---

## Tests de integración

Los tests viven en `tests/test_documentos.py` y cubren los tres endpoints con casos de error:

| Test | Endpoint | Caso |
|---|---|---|
| `test_cargar_documento_pdf_valido` | `POST /cargar` | PDF válido → 200 |
| `test_cargar_documento_tipo_invalido` | `POST /cargar` | `.txt` → 400 |
| `test_cargar_documento_muy_grande` | `POST /cargar` | 6 MB → 400 |
| `test_listar_documentos` | `GET /` | respuesta con `data` y `next_cursor` → 200 |
| `test_listar_documentos_limit_invalido` | `GET /` | `limit=0` → 422 |
| `test_get_documento_no_encontrado` | `GET /id` | UUID inexistente → 404 |
