## Esquema de base de datos

El sistema maneja 6 tablas por el momento,cuentan con aislamiento multi-tenant mediante Row Level Security.

### Diagrama entidad-relación

```mermaid
erDiagram
  organizaciones {
    uuid id PK
    string nombre
    string descripcion
    timestamp created_at
    timestamp updated_at
  }
  usuarios {
    uuid id PK
    string email
    string nombre
    string apellido_paterno
    string apellido_materno
    uuid org_id FK
    uuid rol_id FK
    timestamp created_at
    timestamp updated_at
  }
  roles {
    uuid id PK
    string nombre
  }
  documentos {
    uuid id PK
    string nombre
    string tipo
    string url
    uuid usuario_id FK
    uuid org_id FK
    timestamp created_at
  }
  extracciones {
    uuid id PK
    uuid documento_id FK
    uuid org_id FK
    string uuid_sat
    string rfc_emisor
    string rfc_receptor
    decimal total
    string tipo_comprobante
    timestamp fecha_emision
    jsonb metadatos
    string status
    timestamp created_at
    timestamp updated_at
  }
  conversaciones {
    uuid id PK
    uuid usuario_id FK
    uuid org_id FK
    text mensaje_usuario
    text mensaje_sistema
    timestamp created_at
  }
  organizaciones ||--o{ usuarios : "tiene"
  organizaciones ||--o{ documentos : "tiene"
  organizaciones ||--o{ extracciones : "tiene"
  organizaciones ||--o{ conversaciones : "tiene"
  roles ||--o{ usuarios : "asigna"
  usuarios ||--o{ documentos : "sube"
  usuarios ||--o{ conversaciones : "inicia"
  documentos ||--o{ extracciones : "genera"
```

### Roles y permisos

| Rol | Acceso |
|---|---|
| `owner` | Todo el sistema sin restricción de organización |
| `admin` | Todo dentro de su organización |
| `usuario` | Solo sus propios datos dentro de su organización |

