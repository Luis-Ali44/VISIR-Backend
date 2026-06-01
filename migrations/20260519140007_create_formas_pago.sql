CREATE TABLE formas_pago (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clave  int NOT NULL UNIQUE,
    nombre varchar(255) NOT NULL
);
