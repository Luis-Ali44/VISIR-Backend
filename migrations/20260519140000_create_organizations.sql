CREATE TABLE organizaciones (
    id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre  text not null,
    descripcion text,
    created_at  timestamp not null default now(),
    updated_at  timestamp not null default now()
);