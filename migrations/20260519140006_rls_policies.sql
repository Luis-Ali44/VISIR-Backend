ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;
ALTER table roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;
ALTER table extracciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversaciones ENABLE ROW LEVEL SECURITY;

--sql por que no usamos logica muy compleja
--funcione spara id y rol 
CREATE OR REPLACE FUNCTION get_my_org_id()
RETURNS UUID AS $$
  SELECT (auth.jwt() -> 'user_metadata' ->> 'org_id')::UUID;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION get_my_role()
RETURNS TEXT AS $$
  SELECT auth.jwt() -> 'user_metadata' ->> 'role';
$$ LANGUAGE sql STABLE;


-- organizaciones
CREATE POLICY "owner: todas las organizaciones"
ON organizaciones FOR ALL
USING (get_my_role() = 'owner' AND id = get_my_org_id());

CREATE POLICY "admin: ver su organizacion"
ON organizaciones FOR ALL
USING(get_my_role()= 'admin' AND id=get_my_org_id());


-- roles
CREATE POLICY "owner: todos los roles"
ON roles FOR ALL
USING (get_my_role() = 'owner');

CREATE POLICY "admin: ver roles"
ON roles FOR SELECT
USING (get_my_role()= 'admin');


-- usuarios
CREATE POLICY "owner: todos los usuarios"
ON usuarios FOR ALL
USING (get_my_role() = 'owner');

CREATE POLICY "admin: usuarios de su org"
ON usuarios FOR ALL
USING (get_my_role() = 'admin' AND org_id = get_my_org_id());

CREATE POLICY "usuario: su propio perfil"
ON usuarios FOR SELECT
USING (get_my_role() = 'usuario' AND id = auth.uid());


-- documentos
CREATE POLICY "owner: todos los documentos"
ON documentos FOR ALL
USING (get_my_role() = 'owner');

CREATE POLICY "admin: documentos de su org"
ON documentos FOR ALL
USING (get_my_role() = 'admin' AND org_id = get_my_org_id());

CREATE POLICY "usuario: sus documentos"
ON documentos FOR ALL
USING (get_my_role() = 'usuario' AND usuario_id = auth.uid() AND org_id = get_my_org_id());


-- extracciones
CREATE POLICY "owner: todas las extracciones"
ON extracciones FOR ALL
USING (get_my_role() = 'owner');

CREATE POLICY "admin: extracciones de su org"
ON extracciones FOR ALL
USING (get_my_role() = 'admin' AND org_id = get_my_org_id());

CREATE POLICY "usuario: ver sus extracciones"
ON extracciones FOR SELECT
USING (get_my_role() = 'usuario' AND org_id = get_my_org_id());


-- conversaciones
CREATE POLICY "owner: todas las conversaciones"
ON conversaciones FOR ALL
USING (get_my_role() = 'owner');

CREATE POLICY "admin: conversaciones de su org"
ON conversaciones FOR ALL
USING (get_my_role() = 'admin' AND org_id = get_my_org_id());

CREATE POLICY "usuario: sus conversaciones"
ON conversaciones FOR ALL
USING (get_my_role() = 'usuario' AND usuario_id = auth.uid() AND org_id = get_my_org_id());
