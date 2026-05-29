create table emisores(
id uuid primary key default gen_random_uuid(),
rfc varchar(255) not null,
nombre varchar(255) not null,
apellido_materno varchar(255) not null,
apellido_paterno varchar(255) not null
);