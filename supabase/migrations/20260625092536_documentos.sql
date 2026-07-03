CREATE TABLE documentos (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          varchar(255) NOT NULL,
    tipo            varchar(255) NOT NULL,
    tamaño          int,
    link            varchar(255) NOT NULL,
    id_usuario      uuid REFERENCES usuarios(id) ON DELETE RESTRICT,
    id_organizacion uuid REFERENCES organizaciones(id) ON DELETE RESTRICT,
    id_categorias   uuid REFERENCES categorias(id) ON DELETE RESTRICT,
    created_at      timestamp NOT NULL DEFAULT now()
);
