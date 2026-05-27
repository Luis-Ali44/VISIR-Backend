create table fornmas_pago (
    id uuid primary key gen_random_uuid(),
    clave int not null unique,
    nombre varchar(50) not null 
);