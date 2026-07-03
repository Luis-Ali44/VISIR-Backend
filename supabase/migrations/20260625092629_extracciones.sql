CREATE TABLE extracciones (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    folio_fiscal     varchar(255),
    total            decimal(12, 2),
    metadatos        jsonb,
    fecha_emision    timestamp,
    tipo_comprobante varchar(100),
    metodo_pago      varchar(10),
    estado           varchar(50) DEFAULT 'procesado',
    rfc_emisor       varchar(20),
    nombre_emisor    varchar(255),
    rfc_receptor     varchar(20),
    nombre_receptor  varchar(255),
    id_documento     uuid NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    id_organizacion  uuid NOT NULL REFERENCES organizaciones(id) ON DELETE RESTRICT,
    forma_pago       varchar(150),
    created_at       timestamp NOT NULL DEFAULT now(),
    updated_at       timestamp NOT NULL DEFAULT now()
);
