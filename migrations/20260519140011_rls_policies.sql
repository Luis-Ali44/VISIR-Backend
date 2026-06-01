ALTER TABLE organizaciones  ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles            ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias       ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios         ENABLE ROW LEVEL SECURITY;
ALTER TABLE formas_pago      ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos       ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracciones     ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversaciones   ENABLE ROW LEVEL SECURITY;


GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE ON usuarios       TO authenticated;
GRANT SELECT                 ON organizaciones TO authenticated;
GRANT SELECT                 ON roles          TO authenticated;
GRANT SELECT                 ON categorias     TO authenticated;
GRANT SELECT                 ON formas_pago    TO authenticated;
GRANT SELECT, INSERT         ON documentos     TO authenticated;
GRANT SELECT                 ON extracciones   TO authenticated;
GRANT SELECT, INSERT         ON conversaciones TO authenticated;

GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;


CREATE OR REPLACE FUNCTION get_my_org_id()
RETURNS UUID AS $$
    SELECT (auth.jwt() -> 'user_metadata' ->> 'org_id')::UUID;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_my_role()
RETURNS TEXT AS $$
    SELECT auth.jwt() -> 'user_metadata' ->> 'role';
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- organizaciones
CREATE POLICY "owner: todas las organizaciones"
ON organizaciones FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: su organizacion"
ON organizaciones FOR ALL
USING (get_my_role() = 'admin' AND id = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id = get_my_org_id());

CREATE POLICY "usuario: ver su organizacion"
ON organizaciones FOR SELECT
USING (get_my_role() = 'usuario' AND id = get_my_org_id());

-- roles
CREATE POLICY "owner: todos los roles"
ON roles FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver roles"
ON roles FOR SELECT USING (get_my_role() = 'admin');

CREATE POLICY "usuario: ver roles"
ON roles FOR SELECT USING (get_my_role() = 'usuario');

-- categorias
CREATE POLICY "owner: todas las categorias"
ON categorias FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver categorias"
ON categorias FOR SELECT USING (get_my_role() = 'admin');

CREATE POLICY "usuario: ver categorias"
ON categorias FOR SELECT USING (get_my_role() = 'usuario');

-- usuarios
CREATE POLICY "owner: todos los usuarios"
ON usuarios FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: usuarios de su org"
ON usuarios FOR ALL
USING (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: su propio perfil"
ON usuarios FOR SELECT
USING (get_my_role() = 'usuario' AND id = auth.uid());

CREATE POLICY "usuario: actualizar su propio perfil"
ON usuarios FOR UPDATE
USING (get_my_role() = 'usuario' AND id = auth.uid())
WITH CHECK (get_my_role() = 'usuario' AND id = auth.uid());

-- formas_pago
CREATE POLICY "owner: todas las formas de pago"
ON formas_pago FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver formas de pago"
ON formas_pago FOR SELECT USING (get_my_role() = 'admin');

CREATE POLICY "usuario: ver formas de pago"
ON formas_pago FOR SELECT USING (get_my_role() = 'usuario');

-- documentos
CREATE POLICY "owner: todos los documentos"
ON documentos FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: documentos de su org"
ON documentos FOR ALL
USING (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: sus documentos"
ON documentos FOR ALL
USING (get_my_role() = 'usuario' AND id_usuario = auth.uid() AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'usuario' AND id_usuario = auth.uid() AND id_organizacion = get_my_org_id());

-- extracciones
CREATE POLICY "owner: todas las extracciones"
ON extracciones FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: extracciones de su org"
ON extracciones FOR ALL
USING (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: ver extracciones de su org"
ON extracciones FOR SELECT
USING (get_my_role() = 'usuario' AND id_organizacion = get_my_org_id());

-- conversaciones
CREATE POLICY "owner: todas las conversaciones"
ON conversaciones FOR ALL
USING (get_my_role() = 'owner') WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: conversaciones de su org"
ON conversaciones FOR ALL
USING (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: sus conversaciones"
ON conversaciones FOR ALL
USING (get_my_role() = 'usuario' AND id_usuario = auth.uid() AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'usuario' AND id_usuario = auth.uid() AND id_organizacion = get_my_org_id());
