-- organizaciones
INSERT INTO organizaciones (id, nombre, descripcion) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Empresa Alpha', 'Organización de prueba A'),
  ('22222222-2222-2222-2222-222222222222', 'Empresa Beta', 'Organización de prueba B');

-- roles
INSERT INTO roles (id, nombre) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'owner'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'admin'),
  ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'usuario');

-- usuarios (los ids deben coincidir con los de auth.users en Supabase)
INSERT INTO usuarios (id, email, nombre, apellido_paterno, apellido_materno, org_id, rol_id) VALUES
  -- Alpha
  ('00000001-0000-0000-0000-000000000001', 'owner@alpha.com',   'Luis',    'Rios',    'Torres', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
  ('00000001-0000-0000-0000-000000000002', 'admin@alpha.com',   'Carlos',  'Lopez',   'Ruiz',   '11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
  ('00000001-0000-0000-0000-000000000003', 'usuario@alpha.com', 'Ana',     'Garcia',  'Perez',  '11111111-1111-1111-1111-111111111111', 'cccccccc-cccc-cccc-cccc-cccccccccccc'),
  -- Beta
  ('00000002-0000-0000-0000-000000000001', 'owner@beta.com',    'Maria',   'Mendez',  'Cruz',   '22222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
  ('00000002-0000-0000-0000-000000000002', 'admin@beta.com',    'Pedro',   'Sanchez',  null,    '22222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
  ('00000002-0000-0000-0000-000000000003', 'usuario@beta.com',  'Sofia',   'Ramirez', 'Vega',   '22222222-2222-2222-2222-222222222222', 'cccccccc-cccc-cccc-cccc-cccccccccccc');

-- documentos
INSERT INTO documentos (id, nombre, tipo, url, usuario_id, org_id) VALUES
  -- Alpha
  ('dddddd01-0000-0000-0000-000000000001', 'factura_enero.xml', 'xml', 'https://storage.supabase.co/alpha/factura_enero.xml', '00000001-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111'),
  ('dddddd01-0000-0000-0000-000000000002', 'factura_enero.pdf', 'pdf', 'https://storage.supabase.co/alpha/factura_enero.pdf', '00000001-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111'),
  -- Beta
  ('dddddd02-0000-0000-0000-000000000001', 'recibo_marzo.xml',  'xml', 'https://storage.supabase.co/beta/recibo_marzo.xml',  '00000002-0000-0000-0000-000000000003', '22222222-2222-2222-2222-222222222222'),
  ('dddddd02-0000-0000-0000-000000000002', 'recibo_marzo.pdf',  'pdf', 'https://storage.supabase.co/beta/recibo_marzo.pdf',  '00000002-0000-0000-0000-000000000003', '22222222-2222-2222-2222-222222222222');

-- extracciones
INSERT INTO extracciones (documento_id, org_id, uuid_sat, rfc_emisor, rfc_receptor, total, tipo_comprobante, fecha_emision, status) VALUES
  ('dddddd01-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'AAA-111-BBB', 'XAXX010101000', 'XEXX010101000', 1500.00, 'Ingreso', '2026-01-15 10:00:00', 'procesado'),
  ('dddddd02-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'CCC-333-DDD', 'XAXX020202000', 'XEXX020202000', 3200.00, 'Egreso',  '2026-03-10 09:00:00', 'procesado');