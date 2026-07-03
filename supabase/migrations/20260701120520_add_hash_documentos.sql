ALTER TABLE documentos
ADD COLUMN hash_archivo varchar(225);

CREATE INDEX idx_documentos_hash_archivo ON documentos(hash_archivo);