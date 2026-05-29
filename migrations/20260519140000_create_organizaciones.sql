CREATE TABLE organizaciones (
    id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre  varchar(255) not null,
    descripcion varchar(255)not null,
    created_at  timestamp not null default now(),
    updated_at  timestamp not null default now()
);