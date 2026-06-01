CREATE TABLE extracciones (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    folio_fiscal     varchar(255) NOT NULL,
    total            decimal(10, 2) NOT NULL,
    metadatos        jsonb,
    fecha_emision    timestamp NOT NULL,
    tipo_comprobante varchar(50) NOT NULL CHECK (tipo_comprobante IN ('Ingreso', 'Egreso', 'Traslado', 'Nómina', 'Pago', 'Retención e información de pagos')),
    metodo_pago      varchar(10) NOT NULL CHECK (metodo_pago IN ('PUE', 'PPD')),
    estado           varchar(100) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'procesado', 'error')),
    rfc_emisor       varchar(15) NOT NULL,
    nombre_emisor    varchar(255) NOT NULL,
    rfc_receptor     varchar(15) NOT NULL,
    nombre_receptor  varchar(255) NOT NULL,
    id_documento     uuid NOT NULL REFERENCES documentos(id) ON DELETE RESTRICT,
    id_organizacion  uuid NOT NULL REFERENCES organizaciones(id) ON DELETE RESTRICT,
    id_forma_pago    uuid NOT NULL REFERENCES formas_pago(id) ON DELETE RESTRICT,
    created_at       timestamp NOT NULL DEFAULT now(),
    updated_at       timestamp NOT NULL DEFAULT now()
);
