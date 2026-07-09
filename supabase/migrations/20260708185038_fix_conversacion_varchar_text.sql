ALTER TABLE conversaciones
    RENAME COLUMN mensaje_sistema TO respuesta_sistema;

ALTER TABLE conversaciones
    ALTER COLUMN mensaje_usuario TYPE TEXT,
    ALTER COLUMN respuesta_sistema TYPE TEXT;
