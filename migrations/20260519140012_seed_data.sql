-- solo desarrollo — no correr en producción

-- roles del sistema
INSERT INTO roles (id, nombre) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'owner'),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'admin'),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'usuario');

-- categorias de documentos fiscales
INSERT INTO categorias (id, nombre) VALUES
    ('cat00001-0000-0000-0000-000000000001', 'Factura'),
    ('cat00001-0000-0000-0000-000000000002', 'Nota de crédito'),
    ('cat00001-0000-0000-0000-000000000003', 'Nota de débito'),
    ('cat00001-0000-0000-0000-000000000004', 'Recibo de nómina'),
    ('cat00001-0000-0000-0000-000000000005', 'Carta porte'),
    ('cat00001-0000-0000-0000-000000000006', 'Complemento de pago');

-- catálogo SAT de formas de pago
INSERT INTO formas_pago (id, clave, nombre) VALUES
    ('fp000001-0000-0000-0000-000000000001', 1,  'Efectivo'),
    ('fp000001-0000-0000-0000-000000000002', 2,  'Cheque nominativo'),
    ('fp000001-0000-0000-0000-000000000003', 3,  'Transferencia electrónica de fondos'),
    ('fp000001-0000-0000-0000-000000000004', 4,  'Tarjeta de crédito'),
    ('fp000001-0000-0000-0000-000000000005', 5,  'Monedero electrónico'),
    ('fp000001-0000-0000-0000-000000000006', 6,  'Dinero electrónico'),
    ('fp000001-0000-0000-0000-000000000007', 8,  'Vales de despensa'),
    ('fp000001-0000-0000-0000-000000000008', 12, 'Dación en pago'),
    ('fp000001-0000-0000-0000-000000000009', 13, 'Pago por subrogación'),
    ('fp000001-0000-0000-0000-000000000010', 14, 'Pago por consignación'),
    ('fp000001-0000-0000-0000-000000000011', 15, 'Condonación'),
    ('fp000001-0000-0000-0000-000000000012', 17, 'Compensación'),
    ('fp000001-0000-0000-0000-000000000013', 23, 'Novación'),
    ('fp000001-0000-0000-0000-000000000014', 24, 'Confusión'),
    ('fp000001-0000-0000-0000-000000000015', 25, 'Remisión de deuda'),
    ('fp000001-0000-0000-0000-000000000016', 26, 'Prescripción o caducidad'),
    ('fp000001-0000-0000-0000-000000000017', 27, 'A satisfacción del acreedor'),
    ('fp000001-0000-0000-0000-000000000018', 28, 'Tarjeta de débito'),
    ('fp000001-0000-0000-0000-000000000019', 29, 'Tarjeta de servicios'),
    ('fp000001-0000-0000-0000-000000000020', 30, 'Aplicación de anticipos'),
    ('fp000001-0000-0000-0000-000000000021', 31, 'Intermediario pagos'),
    ('fp000001-0000-0000-0000-000000000022', 99, 'Por definir');

-- organizaciones de prueba
INSERT INTO organizaciones (id, nombre, descripcion) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Empresa Alpha', 'Organización de prueba A'),
    ('22222222-2222-2222-2222-222222222222', 'Empresa Beta',  'Organización de prueba B');

-- usuarios de prueba
INSERT INTO usuarios (id, nombre, apellido_paterno, apellido_materno, id_role, id_organizacion) VALUES
    ('usr00001-0000-0000-0000-000000000001', 'Luis',   'Rios',    'Torres', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111'),
    ('usr00001-0000-0000-0000-000000000002', 'Ana',    'Garcia',  'Perez',  'cccccccc-cccc-cccc-cccc-cccccccccccc', '11111111-1111-1111-1111-111111111111'),
    ('usr00001-0000-0000-0000-000000000003', 'Carlos', 'Lopez',   'Ruiz',   'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111'),
    ('usr00002-0000-0000-0000-000000000001', 'Maria',  'Mendez',  'Cruz',   'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222'),
    ('usr00002-0000-0000-0000-000000000002', 'Pedro',  'Sanchez',  null,    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222'),
    ('usr00002-0000-0000-0000-000000000003', 'Sofia',  'Ramirez', 'Vega',   'cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222');

-- documentos de prueba para los 3 endpoints
INSERT INTO documentos (id, nombre, tipo, tamaño, link, id_usuario, id_organizacion, id_categorias, created_at) VALUES
    (
        'dddddd01-0000-0000-0000-000000000001',
        'factura_enero_2026.xml',
        'text/xml',
        4096,
        'documentos/factura_enero_2026.xml',
        'usr00001-0000-0000-0000-000000000002',
        '11111111-1111-1111-1111-111111111111',
        'cat00001-0000-0000-0000-000000000001',
        '2026-01-15 10:00:00'
    ),
    (
        'dddddd01-0000-0000-0000-000000000002',
        'factura_enero_2026.pdf',
        'application/pdf',
        98304,
        'documentos/factura_enero_2026.pdf',
        'usr00001-0000-0000-0000-000000000002',
        '11111111-1111-1111-1111-111111111111',
        'cat00001-0000-0000-0000-000000000001',
        '2026-01-15 10:01:00'
    ),
    (
        'dddddd02-0000-0000-0000-000000000001',
        'nomina_febrero_2026.xml',
        'text/xml',
        3072,
        'documentos/nomina_febrero_2026.xml',
        'usr00002-0000-0000-0000-000000000003',
        '22222222-2222-2222-2222-222222222222',
        'cat00001-0000-0000-0000-000000000004',
        '2026-02-28 09:00:00'
    ),
    (
        'dddddd02-0000-0000-0000-000000000002',
        'nota_credito_marzo_2026.xml',
        'text/xml',
        2048,
        'documentos/nota_credito_marzo_2026.xml',
        'usr00002-0000-0000-0000-000000000003',
        '22222222-2222-2222-2222-222222222222',
        'cat00001-0000-0000-0000-000000000002',
        '2026-03-10 14:30:00'
    );
