    CREATE TABLE usuarios(
        id      uuid primary key default gen_random_uuid(),
        role_id uuid references roles(id),
        email   text not null unique,
        nombre  text not null, 
        apellido_paterno text not null, 
        apellido_materno text,
        org_id      uuid references organizaciones(id) on delete restrict,
        created_at  timestamp not null default now(),
        updated_at  timestamp not null default now()
    );