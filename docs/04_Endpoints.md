# Endpoints

Base URL: `http://localhost:8000`

Documentación interactiva disponible en `http://localhost:8000/docs` (Swagger UI).

---

## General

### `GET /health`
Verifica que el servidor está corriendo.

**Respuesta `200`**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

### `GET /supabase`
Prueba de conexión a Supabase. Devuelve todas las organizaciones.

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
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo | ✅ | PDF o XML, máximo 5 MB |

**Tipos permitidos**
- `application/pdf`
- `text/xml`

**Respuesta `200`**
```json
{
  "messege": "archivo guardado",
  "archivo guardado": "uuid-nombre_archivo.pdf",
  "metadata": {
    "nombre": "factura.pdf",
    "tipo": "application/pdf",
    "tamaño": 102400,
    "link": "uuid-factura.pdf"
  }
}
```

**Errores**
| Código | Motivo |
|---|---|
| `400` | Tipo de archivo no permitido |
| `400` | Archivo mayor a 5 MB |

---

### `GET /v1/documentos`
Lista documentos con paginación por cursor.

**Query params**
| Param | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | int | `10` | Cantidad de resultados (1–50) |
| `cursor` | string | `null` | `created_at` del último elemento recibido |

**Respuesta `200`**
```json
{
  "data": [
    {
      "id": "uuid",
      "nombre": "factura.pdf",
      "tipo": "application/pdf",
      "tamaño": 102400,
      "link": "uuid-factura.pdf",
      "id_usuario": "uuid",
      "id_organizacion": "uuid",
      "created_at": "2026-05-19T14:00:00"
    }
  ],
  "next_cursor": "2026-05-19T14:00:00"
}
```

> Cuando `next_cursor` es `null` no hay más páginas.

---

### `GET /v1/documentos/id`
Obtiene un documento por su ID.

**Query params**
| Param | Tipo | Requerido | Descripción |
|---|---|---|---|
| `document_id` | string (UUID) | ✅ | ID del documento |

**Respuesta `200`**
```json
[
  {
    "id": "uuid",
    "nombre": "factura.pdf",
    "tipo": "application/pdf",
    "tamaño": 102400,
    "link": "uuid-factura.pdf",
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

## Paginación por cursor

La lista de documentos usa cursor-based pagination en lugar de offset para evitar duplicados cuando se insertan registros entre páginas.

**Primera página**
```
GET /v1/documentos?limit=10
```

**Página siguiente** — usar el `next_cursor` de la respuesta anterior
```
GET /v1/documentos?limit=10&cursor=2026-05-19T14:00:00
```

Cuando `next_cursor` es `null`, se llegó al final.
