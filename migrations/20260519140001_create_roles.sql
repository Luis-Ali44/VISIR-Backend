CREATE TABLE roles(
id uuid primary key default gen_random_uuid(),
nombre text not null
);