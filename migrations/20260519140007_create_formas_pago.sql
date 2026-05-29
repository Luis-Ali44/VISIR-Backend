create table FormasPagos(
    id uuid primary key default gen_random_uuid(),
    clave int not null unique,
    nombre varchar(255) not null
);