create table emisores(
id uuid primary key gen_random_uuid(),
rfc varchar(255),
nombre varchar(255),
apellido_materno varchar(255),
apellido_paterno varchar(255)
);