CREATE TABLE extracciones (
    id               uuid primary key default gen_random_uuid(),
    folio_fiscal     varchar(255),
    total            decimal(10, 2),
    tipo_comprobante check(tipo_comprobante IN("Ingreso", "Egreso", "Traslado", "Nómina", "Pago", "Retencon e información de pagos")),
    metodo_pago      check(metodo_pago IN("PUE", "PPD" )),
    fecha_emision    timestamp,
    metadatos        jsonb,
    estado           varchar(100) default "pendiente" check(estado in ("pendiente", "procesado", "error")),
    id_emisor        uuid references emisores(id) on delete restrict,
    id_receptor      uuid references receptores(id) on delete restrict,
    id_documento     uuid references documentos(id) on delete restrict,
    id_organizacion  uuid references organizaciones(id) on delete restrict,
    id_forma_pago    text references formas_pago(id) on delete restrict,
    created_at       timestamp not null default now(),
    updated_at       timestamp not null default now()
);