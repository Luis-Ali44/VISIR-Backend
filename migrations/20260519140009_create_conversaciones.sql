CREATE TABLE conversaciones (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    id_usuario      uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    id_organizacion uuid NOT NULL REFERENCES organizaciones(id) ON DELETE RESTRICT,
    mensaje_usuario varchar(255),
    mensaje_sistema varchar(255),
    created_at      timestamp NOT NULL DEFAULT now()
);
