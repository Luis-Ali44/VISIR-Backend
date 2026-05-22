CREATE TABLE extracciones (
    id               uuid primary key default gen_random_uuid(),
    documento_id     uuid not null references documentos(id) on delete restrict,
    org_id           uuid not null references organizaciones(id) on delete restrict,
    uuid_sat         text,
    rfc_emisor       text,
    rfc_receptor     text,
    total            decimal,
    tipo_comprobante text, -- Ingreso, Egreso, Traslado, Nómina, Pago
    fecha_emision    timestamp,
    metadatos        jsonb,
    status           text not null default 'pendiente', -- pendiente, procesado, error
    created_at       timestamp not null default now(),
    updated_at       timestamp not null default now()
);

--Posiblemente deberiaos de separar extracciones en 3 tablas, extraccion, receptor, emisor