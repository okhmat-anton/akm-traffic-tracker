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
    '01a19e62a9d37723eb94af002a3782a4', /* akm_ + admin */
    TRUE,
    TRUE
);
