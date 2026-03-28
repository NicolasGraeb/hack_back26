-- Schemat: users 1:1 companies, companies 1:N announcements, companies M:N categories
-- PostgreSQL

CREATE TABLE users (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    surname    TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE
);

CREATE TABLE companies (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    nip_krs         TEXT NOT NULL UNIQUE,
    user_id         BIGINT NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
    address         TEXT,
    image_url       TEXT,
    contact_phone   TEXT,
    contact_email   TEXT
);

CREATE TABLE categories (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE
);

-- Relacja wiele-do-wielu: firma ↔ kategorie
CREATE TABLE company_categories (
    company_id  BIGINT NOT NULL REFERENCES companies (id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories (id) ON DELETE CASCADE,
    PRIMARY KEY (company_id, category_id)
);

CREATE INDEX idx_company_categories_category ON company_categories (category_id);

CREATE TABLE announcements (
    id          BIGSERIAL PRIMARY KEY,
    company_id  BIGINT NOT NULL REFERENCES companies (id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Widełki opcjonalne; szczegóły, wymagania (np. przestrzeń biurowa) — w opisie
    salary_min  NUMERIC(12, 2),
    salary_max  NUMERIC(12, 2),
    description TEXT
);

CREATE INDEX idx_announcements_company ON announcements (company_id);
