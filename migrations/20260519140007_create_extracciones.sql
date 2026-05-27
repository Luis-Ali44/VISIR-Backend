CREATE TABLE extracciones (
    id               uuid primary key default gen_random_uuid(),
    folio_fiscal     varchar(255) not null,
    total            decimal(10, 2) not null,
    metadatos        jsonb,
    fecha_emision    timestamp not null,
    tipo_comprobante check(tipo_comprobante IN(Ingreso, 'Egreso', 'Traslado', 'Nómina', 'Pago', 'Retencon e información de pagos')) not null,
    metodo_pago      check(metodo_pago IN('PUE', 'PPD' )) not null,
    estado           varchar(100) default 'pendiente' check(estado in ('pendiente', 'procesado', 'error')) not null,
    id_emisor        uuid references emisores(id) on delete restrict not null,
    id_receptor      uuid references receptores(id) on delete restrict not null,
    id_documento     uuid references documentos(id) on delete restrict not null,
    id_organizacion  uuid references organizaciones(id) on delete restrict not null,
    id_forma_pago    uuid references FormasPagos(id) on delete restrict not null,
    created_at       timestamp not null default now(),
    updated_at       timestamp not null default now()
);  