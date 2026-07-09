alter table documentos
    add column estado_documento varchar(50) default 'pendiente' not null;