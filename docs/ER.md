# Base de datos

Visir usa Supabase (PostgreSQL). El aislamiento multi-tenant se implementa con Row Level Security — cada fila solo es visible para el usuario o la organización que le corresponde.

Las migraciones viven en `migrations/` y se aplican en orden desde el SQL Editor de Supabase.

---

## Orden de migraciones

| Archivo | Tabla |
|---|---|
| `20260519140000_create_organizaciones.sql` | `organizaciones` |
| `20260519140001_create_roles.sql` | `roles` |
| `20260519140002_create_categorias.sql` | `categorias` |
| `20260519140003_create_usuarios.sql` | `usuarios` |
| `20260519140004_create_emisores.sql` | `emisores` |
| `20260519140006_create_receptores.sql` | `receptores` |
| `20260519140007_create_formas_pago.sql` | `formas_pago` |
| `20260519140008_create_documentos.sql` | `documentos` |
| `20260519140009_create_conversaciones.sql` | `conversaciones` |
| `20260519140010_create_extracciones.sql` | `extracciones` |
| `20260519140011_rls_policies.sql` | RLS, trigger, grants |
| `20260519140012_seed_data.sql` | Datos de prueba |

---

## Diagrama entidad-relación

```mermaid
erDiagram
  organizaciones {
    uuid id PK
    varchar nombre
    varchar descripcion
    timestamp created_at
    timestamp updated_at
  }

  roles {
    uuid id PK
    varchar nombre
  }

  categorias {
    uuid id PK
    varchar nombre
  }

  usuarios {
    uuid id PK
    varchar nombre
    varchar apellido_paterno
    varchar apellido_materno
    uuid id_role FK
    uuid id_organizacion FK
    boolean activa
    timestamp created_at
    timestamp updated_at
  }

  emisores {
    uuid id PK
    varchar rfc
    varchar nombre
    varchar apellido_paterno
    varchar apellido_materno
  }

  receptores {
    uuid id PK
    varchar rfc
    varchar nombre
    varchar apellido_paterno
    varchar apellido_materno
  }

  formas_pago {
    uuid id PK
    int clave
    varchar nombre
  }

  documentos {
    uuid id PK
    varchar nombre
    varchar tipo
    int tamaño
    varchar link
    uuid id_usuario FK
    uuid id_organizacion FK
    uuid id_categorias FK
    timestamp created_at
  }

  extracciones {
    uuid id PK
    varchar folio_fiscal
    decimal total
    jsonb metadatos
    timestamp fecha_emision
    varchar tipo_comprobante
    varchar metodo_pago
    varchar estado
    uuid id_emisor FK
    uuid id_receptor FK
    uuid id_documento FK
    uuid id_organizacion FK
    uuid id_forma_pago FK
    timestamp created_at
    timestamp updated_at
  }

  conversaciones {
    uuid id PK
    uuid id_usuario FK
    uuid id_organizacion FK
    varchar mensaje_usuario
    varchar mensaje_sistema
    timestamp created_at
  }

  organizaciones ||--o{ usuarios       : "tiene"
  organizaciones ||--o{ documentos     : "tiene"
  organizaciones ||--o{ extracciones   : "tiene"
  organizaciones ||--o{ conversaciones : "tiene"
  roles          ||--o{ usuarios       : "asigna"
  categorias     ||--o{ documentos     : "clasifica"
  usuarios       ||--o{ documentos     : "sube"
  usuarios       ||--o{ conversaciones : "inicia"
  documentos     ||--o{ extracciones   : "genera"
  emisores       ||--o{ extracciones   : "emite"
  receptores     ||--o{ extracciones   : "recibe"
  formas_pago    ||--o{ extracciones   : "clasifica"
```

---

### Permisos por tabla

| Tabla | owner | admin | usuario |
|---|---|---|---|
| `organizaciones` | CRUD total | CRUD su org | Solo lectura su org |
| `roles` | CRUD total | Solo lectura | Solo lectura |
| `categorias` | CRUD total | Solo lectura | Solo lectura |
| `usuarios` | CRUD total | CRUD su org | Ver y editar su propio perfil |
| `emisores` | CRUD total | Ver e insertar | Solo lectura |
| `receptores` | CRUD total | Ver e insertar | Solo lectura |
| `formas_pago` | CRUD total | Solo lectura | Solo lectura |
| `documentos` | CRUD total | CRUD su org | CRUD sus docs en su org |
| `extracciones` | CRUD total | CRUD su org | Solo lectura su org |
| `conversaciones` | CRUD total | CRUD su org | CRUD sus conversaciones en su org |

---

## Valores válidos en extracciones

**`tipo_comprobante`**:
`'Ingreso'`, `'Egreso'`, `'Traslado'`, `'Nómina'`, `'Pago'`, `'Retención e información de pagos'`

**`metodo_pago`**: `'PUE'` (pago en una sola exhibición), `'PPD'` (pago en parcialidades o diferido)

**`estado`**: `'pendiente'` (default), `'procesado'`, `'error'`
