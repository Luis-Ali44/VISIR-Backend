-- Roles:
--   owner   → dueño del sistema, acceso total a TODO
--   admin   → admin de su organización 
--   usuario → usuario normal, acceso limitado dentro de su org

ALTER TABLE organizaciones   ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles             ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias        ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios          ENABLE ROW LEVEL SECURITY;
ALTER TABLE emisores          ENABLE ROW LEVEL SECURITY;
ALTER TABLE formas_pago       ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos        ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracciones      ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversaciones    ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION get_my_org_id()
RETURNS UUID AS $$
  SELECT (auth.jwt() -> 'user_metadata' ->> 'org_id')::UUID;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_my_role()
RETURNS TEXT AS $$
  SELECT auth.jwt() -> 'user_metadata' ->> 'role';
$$ LANGUAGE sql STABLE SECURITY DEFINER;



-- ORGANIZACIONES
-- owner → ve y gestiona TODAS las organizaciones
-- admin → solo ve y edita SU organización
-- usuario → solo puede ver SU organización (sin modificar)


CREATE POLICY "owner: todas las organizaciones"
ON organizaciones FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: su organizacion"
ON organizaciones FOR ALL
USING  (get_my_role() = 'admin' AND id = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id = get_my_org_id());

CREATE POLICY "usuario: ver su organizacion"
ON organizaciones FOR SELECT
USING (get_my_role() = 'usuario' AND id = get_my_org_id());


-- ============================================================
-- ROLES
-- owner → CRUD total
-- admin → solo lectura (necesita saber qué roles existen)
-- usuario → solo lectura
-- ============================================================

CREATE POLICY "owner: todos los roles"
ON roles FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver roles"
ON roles FOR SELECT
USING (get_my_role() = 'admin');

CREATE POLICY "usuario: ver roles"
ON roles FOR SELECT
USING (get_my_role() = 'usuario');


-- ============================================================
-- CATEGORIAS
-- owner → CRUD total
-- admin → solo lectura
-- usuario → solo lectura
-- ============================================================

CREATE POLICY "owner: todas las categorias"
ON categorias FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver categorias"
ON categorias FOR SELECT
USING (get_my_role() = 'admin');

CREATE POLICY "usuario: ver categorias"
ON categorias FOR SELECT
USING (get_my_role() = 'usuario');


-- ============================================================
-- USUARIOS
-- owner → CRUD total sobre todos los usuarios
-- admin → CRUD sobre usuarios de SU organización
-- usuario → solo puede ver y editar SU propio perfil
-- ============================================================

CREATE POLICY "owner: todos los usuarios"
ON usuarios FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: usuarios de su org"
ON usuarios FOR ALL
USING  (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: su propio perfil"
ON usuarios FOR SELECT
USING (get_my_role() = 'usuario' AND id = auth.uid());

CREATE POLICY "usuario: actualizar su propio perfil"
ON usuarios FOR UPDATE
USING  (get_my_role() = 'usuario' AND id = auth.uid())
WITH CHECK (get_my_role() = 'usuario' AND id = auth.uid());


-- ============================================================
-- EMISORES
-- owner → CRUD total
-- admin → CRUD dentro de su org (emisores son globales,
--         admin puede crear/ver pero no borrar)
-- usuario → solo lectura
-- ============================================================

CREATE POLICY "owner: todos los emisores"
ON emisores FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver y crear emisores"
ON emisores FOR SELECT
USING (get_my_role() = 'admin');

CREATE POLICY "admin: insertar emisores"
ON emisores FOR INSERT
WITH CHECK (get_my_role() = 'admin');

CREATE POLICY "usuario: ver emisores"
ON emisores FOR SELECT
USING (get_my_role() = 'usuario');


-- ============================================================
-- FORMAS DE PAGO
-- Tabla catálogo, solo owner puede modificarla
-- admin y usuario solo lectura
-- ============================================================

CREATE POLICY "owner: todas las formas de pago"
ON formas_pago FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: ver formas de pago"
ON formas_pago FOR SELECT
USING (get_my_role() = 'admin');

CREATE POLICY "usuario: ver formas de pago"
ON formas_pago FOR SELECT
USING (get_my_role() = 'usuario');


-- ============================================================
-- DOCUMENTOS
-- owner → CRUD total
-- admin → CRUD sobre documentos de SU organización
-- usuario → CRUD sobre SUS documentos dentro de su org
-- ============================================================

CREATE POLICY "owner: todos los documentos"
ON documentos FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: documentos de su org"
ON documentos FOR ALL
USING  (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: sus documentos"
ON documentos FOR ALL
USING  (get_my_role() = 'usuario' AND usuario_id = auth.uid() AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'usuario' AND usuario_id = auth.uid() AND id_organizacion = get_my_org_id());


-- ============================================================
-- EXTRACCIONES
-- owner → CRUD total
-- admin → CRUD sobre extracciones de SU organización
-- usuario → solo lectura sobre extracciones de su org
-- ============================================================

CREATE POLICY "owner: todas las extracciones"
ON extracciones FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: extracciones de su org"
ON extracciones FOR ALL
USING  (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: ver extracciones de su org"
ON extracciones FOR SELECT
USING (get_my_role() = 'usuario' AND id_organizacion = get_my_org_id());


-- ============================================================
-- CONVERSACIONES
-- owner → CRUD total
-- admin → CRUD sobre conversaciones de SU organización
-- usuario → CRUD sobre SUS conversaciones dentro de su org
-- ============================================================

CREATE POLICY "owner: todas las conversaciones"
ON conversaciones FOR ALL
USING (get_my_role() = 'owner')
WITH CHECK (get_my_role() = 'owner');

CREATE POLICY "admin: conversaciones de su org"
ON conversaciones FOR ALL
USING  (get_my_role() = 'admin' AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'admin' AND id_organizacion = get_my_org_id());

CREATE POLICY "usuario: sus conversaciones"
ON conversaciones FOR ALL
USING  (get_my_role() = 'usuario' AND id_usuario = auth.uid() AND id_organizacion = get_my_org_id())
WITH CHECK (get_my_role() = 'usuario' AND id_usuario = auth.uid() AND id_organizacion = get_my_org_id());
