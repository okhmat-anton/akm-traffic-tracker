CREATE TYPE landing_mood AS ENUM ('link', 'mirror', 'local_file');
CREATE TYPE status_mood AS ENUM ('pending', 'success', 'error');
CREATE TYPE domain_error_handle_mood AS ENUM ('handle', 'error');

-- Создание таблицы пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE
);

-- Создание таблицы проектов
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    name VARCHAR(255) NOT NULL,
    default_redirect_url TEXT,
    settings JSONB
);

-- Связь пользователей и проектов (права доступа)
CREATE TABLE project_users (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_view BOOLEAN DEFAULT TRUE
);

-- Таблица визитов
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    visit_id UUID NOT NULL UNIQUE,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    ip VARCHAR(45),
    user_agent TEXT,
    country_code CHAR(2),
    referer TEXT,
    domain TEXT,
    is_bot BOOLEAN DEFAULT FALSE,
    device_type VARCHAR(50),
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_content VARCHAR(255),
    utm_term VARCHAR(255),
    custom_vars JSONB,
    clicked_element TEXT,
    external_id VARCHAR(255),
    converted BOOLEAN DEFAULT FALSE
);

-- Таблица правил редиректов
CREATE TABLE redirect_rules (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    domain TEXT,
    country_code CHAR(2),
    is_bot BOOLEAN,
    target_url TEXT NOT NULL,
    priority INT DEFAULT 100,
    active BOOLEAN DEFAULT TRUE
);

-- Таблица постбеков
CREATE TABLE postbacks (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT now(),
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    visit_id UUID,
    external_id VARCHAR(255),
    status VARCHAR(50),
    raw_data JSONB
);

CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,                  -- адрес домена
    redirect_https BOOLEAN DEFAULT TRUE,                  -- перенаправлять ли на https
    handle_404 domain_error_handle_mood,                -- 'error' или 'redirect_to_company'
    default_company VARCHAR(255),                         -- компания по умолчанию
    group_name VARCHAR(255),                               -- группа домена
    status status_mood,                  -- статус ('pending', 'ok', 'error')
    created_at TIMESTAMP DEFAULT NOW(),                    -- дата создания
    updated_at TIMESTAMP DEFAULT NOW()                     -- дата обновления
);

CREATE TABLE landings (
    id SERIAL PRIMARY KEY,
    folder VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL UNIQUE,
    link VARCHAR(255),
    type landing_mood,                  -- type ('link', 'mirror', 'file')
    tags VARCHAR(255),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Создание индексов для скорости
CREATE INDEX idx_visits_project_id ON visits (project_id);
CREATE INDEX idx_visits_created_at ON visits (created_at);
CREATE INDEX idx_redirect_rules_project_id ON redirect_rules (project_id);
CREATE INDEX idx_postbacks_project_id ON postbacks (project_id);
CREATE INDEX idx_visits_visit_id ON visits (visit_id);
CREATE INDEX idx_postbacks_visit_id ON postbacks (visit_id);

-- Создание стартового пользователя tracker_admin
INSERT INTO users (username, email, password_hash, is_admin, active)
VALUES (
    'tracker_admin',
    'admin@example.com',
    '5dfc9a6ef90c0908795b917ae279e90a', /* akm_ + admin */
    TRUE,
    TRUE
);
