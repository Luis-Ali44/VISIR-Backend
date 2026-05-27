    CREATE TABLE documentos(
    id      uuid primary key default gen_random_uuid(),
    nombre  varchar(255) not null,
    tipo    varchar(255) not null,  
    url     varchar(255) not null,
    created_at  timestamp not null default now(),
    usuario_id  uuid references usuarios(id) on delete restrict,
    id_organizacion  uuid references organizaciones(id) on delete restrict
    );