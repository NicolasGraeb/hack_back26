-- STARSZY SKRYPT SQL (SoftLab / przykłady). Aktualne demo 10 firm: python utils/seed_demo_data.py
-- lub od zera: python utils/setup_database.py

TRUNCATE announcements, company_categories, companies, categories, users RESTART IDENTITY CASCADE;

INSERT INTO users (name, surname, email) VALUES
    ('Anna', 'Kowalska', 'anna.kowalska@example.com'),
    ('Jan', 'Nowak', 'jan.nowak@example.com'),
    ('Maria', 'Wiśniewska', 'maria.wisniewska@example.com');

INSERT INTO categories (name) VALUES
    ('IT / oprogramowanie'),
    ('Badania i rozwój (B+R)'),
    ('E-commerce'),
    ('Energia odnawialna');

INSERT INTO companies (name, nip_krs, user_id, address, image_url) VALUES
    (
        'SoftLab Sp. z o.o.',
        '5270000001',
        (SELECT id FROM users WHERE email = 'anna.kowalska@example.com'),
        'ul. Innowacji 12, 35-123 Rzeszów',
        NULL
    ),
    (
        'EcoPack Innovations Sp. z o.o.',
        '5270000002',
        (SELECT id FROM users WHERE email = 'jan.nowak@example.com'),
        NULL,
        NULL
    ),
    (
        'Zielony Prąd S.A.',
        '5270000003',
        (SELECT id FROM users WHERE email = 'maria.wisniewska@example.com'),
        'al. Energetyczna 5, 00-001 Warszawa, bud. C, II piętro',
        NULL
    );

INSERT INTO company_categories (company_id, category_id)
SELECT c.id, cat.id
FROM companies c
JOIN categories cat ON cat.name = 'IT / oprogramowanie'
WHERE c.nip_krs = '5270000001'
UNION ALL
SELECT c.id, cat.id
FROM companies c
JOIN categories cat ON cat.name = 'Badania i rozwój (B+R)'
WHERE c.nip_krs = '5270000001'
UNION ALL
SELECT c.id, cat.id
FROM companies c
JOIN categories cat ON cat.name = 'Badania i rozwój (B+R)'
WHERE c.nip_krs = '5270000002'
UNION ALL
SELECT c.id, cat.id
FROM companies c
JOIN categories cat ON cat.name = 'E-commerce'
WHERE c.nip_krs = '5270000002'
UNION ALL
SELECT c.id, cat.id
FROM companies c
JOIN categories cat ON cat.name = 'Energia odnawialna'
WHERE c.nip_krs = '5270000003';

INSERT INTO announcements (company_id, created_at, salary_min, salary_max, description)
SELECT
    c.id,
    TIMESTAMPTZ '2026-03-01 10:00:00+01',
    12000.00,
    18000.00,
    'Backend Python, praca hybrydowa. Dodatkowo: dostęp do sali konferencyjnej i parking dla zespołu.'
FROM companies c
WHERE c.nip_krs = '5270000001'
UNION ALL
SELECT
    c.id,
    TIMESTAMPTZ '2026-03-15 14:30:00+01',
    NULL,
    NULL,
    'Szukamy partnera B+R na wdrożenie linii kompostowalnych opakowań. Ważna przestrzeń magazynowa min. 300 m² oraz dostęp do laboratorium lub możliwość współdzielenia.'
FROM companies c
WHERE c.nip_krs = '5270000002'
UNION ALL
SELECT
    c.id,
    TIMESTAMPTZ '2026-03-20 09:00:00+01',
    9500.00,
    11000.00,
    'Stanowisko: technik utrzymania instalacji PV. Wymagane prawo jazdy kat. B.'
FROM companies c
WHERE c.nip_krs = '5270000003';
