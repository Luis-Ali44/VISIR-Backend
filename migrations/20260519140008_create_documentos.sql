    CREATE TABLE documentos(
    id      uuid primary key default gen_random_uuid(),
    nombre  varchar(255) not null,
    tipo    varchar(255) not null,  
    tamaño gitint,  
    link     varchar(255) not null,
    id_usuario  uuid references usuarios(id) on delete restrict,
    id_organizacion  uuid references organizaciones(id) on delete restrict,
    created_at  timestamp not null default now()
    );