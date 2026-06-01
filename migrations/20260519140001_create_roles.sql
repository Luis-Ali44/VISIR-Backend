CREATE TABLE roles(
id uuid primary key default gen_random_uuid(),
nombre varchar(255) not null
);