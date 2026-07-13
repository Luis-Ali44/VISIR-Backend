CREATE TABLE sesiones_conversacion (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    id_usuario      uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    id_organizacion uuid NOT NULL REFERENCES organizaciones(id) ON DELETE RESTRICT,
    contexto        jsonb,
    created_at      timestamp NOT NULL DEFAULT now()
);

ALTER TABLE conversaciones ADD COLUMN sesion_id uuid;
CREATE INDEX idx_conversaciones_sesion ON conversaciones(sesion_id);

ALTER TABLE sesiones_conversacion ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON sesiones_conversacion TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversaciones       TO authenticated;

CREATE POLICY "owner: todas las sesiones"
    ON sesiones_conversacion FOR ALL
    USING (get_my_role() = 'owner')
    WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: sesiones de su org"
    ON sesiones_conversacion FOR ALL
    USING (
        id_organizacion = get_my_org_id() and
        get_my_role() = 'admin'
    )
    WITH CHECK (
        get_my_role() = 'admin' AND 
        id_organizacion = get_my_org_id()
    );


CREATE POLICY "usuario: sus sesiones"
    ON sesiones_conversacion FOR ALL
    USING (
        id_usuario = auth.uid() and 
        get_my_role() = 'usuario' and
        id_organizacion = get_my_org_id()
    )
    WITH CHECK (
        get_my_role() = 'usuario' AND 
        id_usuario = auth.uid() AND 
        id_organizacion = get_my_org_id()
    );
