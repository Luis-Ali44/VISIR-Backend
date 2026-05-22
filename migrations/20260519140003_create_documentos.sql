    CREATE TABLE documentos(
    id      uuid primary key default gen_random_uuid(),
    nombre  text not null,
    tipo    text not null,     --pdf, xml
    url     text not null,
    usuario_id  uuid references usuarios(id) on delete restrict,
    org_id      uuid references organizaciones(id) on delete restrict,
    created_at  timestamp not null default now()
    );