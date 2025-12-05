-- Миграция: Добавление системы верификации доменов
-- Дата: 2025-12-04

-- 1. Создать таблицу верификаций доменов
CREATE TABLE IF NOT EXISTS domain_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    verification_code VARCHAR(100) UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    verification_method VARCHAR(50),
    verified_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    attempts INTEGER DEFAULT 0 NOT NULL,
    last_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Создать индексы для domain_verifications
CREATE INDEX IF NOT EXISTS idx_domain_verifications_user ON domain_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_domain_verifications_domain ON domain_verifications(domain);
CREATE INDEX IF NOT EXISTS idx_domain_verifications_code ON domain_verifications(verification_code);
CREATE INDEX IF NOT EXISTS idx_domain_verifications_user_domain ON domain_verifications(user_id, domain);

-- 3. Добавить поля верификации в web_scans
ALTER TABLE web_scans 
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS verification_id INTEGER REFERENCES domain_verifications(id) ON DELETE SET NULL;

-- 4. Удалить таблицу file_analyses если существует (больше не используется)
DROP TABLE IF EXISTS file_analyses CASCADE;

COMMIT;
