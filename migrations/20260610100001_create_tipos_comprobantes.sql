create table tipos_comprobantes(
    id uuid primary key default gen_random_uuid(),
    clave varchar(50),
    nombre varchar(255)
);