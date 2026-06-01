CREATE TABLE usuarios (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre           varchar(255) NOT NULL,
    apellido_paterno varchar(255) NOT NULL,
    apellido_materno varchar(255),
    created_at       timestamp NOT NULL DEFAULT now(),
    updated_at       timestamp NOT NULL DEFAULT now(),
    id_role          uuid REFERENCES roles(id),
    id_organizacion  uuid REFERENCES organizaciones(id) ON DELETE RESTRICT,
    activa           boolean DEFAULT true
);