CREATE TABLE conversaciones (
    id               uuid primary key default gen_random_uuid(),
    mensaje_usuario  text not null,
    mensaje_sistema  text not null,
    created_at       timestamp not null default now(),
    id_usuario       uuid not null references usuarios(id) on delete restrict,
    id_organizacion  uuid not null references organizaciones(id) on delete restrict
);