    CREATE TABLE usuarios(
        id      uuid primary key default gen_random_uuid(),
        nombre  varchar(255) not null, 
        apellido_paterno varchar(255) not null, 
        apellido_materno varchar(255) not null,
        created_at  timestamp not null default now(),
        updated_at  timestamp not null default now(),
        id_role uuid references roles(id),
        id_organizacion  uuid references organizaciones(id) on delete restrict
    );  