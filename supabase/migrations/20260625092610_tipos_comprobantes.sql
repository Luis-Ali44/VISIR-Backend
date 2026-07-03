CREATE TABLE tipos_comprobantes (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clave  varchar(50),
    nombre varchar(255)
);
