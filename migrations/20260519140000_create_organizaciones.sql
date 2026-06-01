CREATE TABLE organizaciones (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      varchar(255) NOT NULL,
    descripcion varchar(255),
    created_at  timestamp NOT NULL DEFAULT now(),
    updated_at  timestamp NOT NULL DEFAULT now()
);