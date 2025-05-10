CREATE TYPE landing_mood AS ENUM ('link', 'mirror', 'local_file');
CREATE TYPE status_mood AS ENUM ('pending', 'success', 'error');
CREATE TYPE domain_error_handle_mood AS ENUM ('handle', 'error');
CREATE TYPE campaign_type AS ENUM ('campaign', 'tracking_only');
CREATE TYPE campaign_status AS ENUM ('active', 'paused');
CREATE TYPE redirect_mode AS ENUM ('position', 'weight');

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





CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,                  -- адрес домена
    redirect_https BOOLEAN DEFAULT TRUE,                  -- перенаправлять ли на https
    handle_404 domain_error_handle_mood,                -- 'error' или 'redirect_to_company'
    default_campaign_id INTEGER,                         -- компания по умолчанию
    group_name VARCHAR(255),                               -- группа домена
    status status_mood,                  -- статус ('pending', 'success', 'error')
    created_at TIMESTAMP DEFAULT NOW(),                    -- дата создания
    updated_at TIMESTAMP DEFAULT NOW()                     -- дата обновления
);

-- Add a demo domain
INSERT INTO domains (domain, redirect_https, handle_404, default_campaign_id, group_name, status, created_at, updated_at)
VALUES
('demo.example.com', TRUE, 'error', NULL, 'Demo Group', 'pending', NOW(), NOW());

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

INSERT INTO landings (folder, name, link, type, tags, created_at, updated_at)
VALUES
('demo_folder', 'Demo Landing', 'https://example.com/demo', 'link', 'demo,example', now(), now());


CREATE TABLE affiliate_networks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    offer_parameters VARCHAR(1024),
    s2s_postback VARCHAR(1024),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);


CREATE TABLE offers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    url TEXT NOT NULL,
    affiliate_network_id INTEGER REFERENCES affiliate_networks(id) ON DELETE SET NULL,
    countries JSONB,                                        -- [{ "code": "US", "priority": 1 }, { "code": "CA" }]
    payout NUMERIC(10, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'active',
    tokens JSONB,
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

INSERT INTO offers (name, url, affiliate_network_id, countries, payout, currency, status, tokens, notes, tags)
VALUES
('Demo Offer 1', 'https://example.com/offer1',
 (SELECT id FROM affiliate_networks WHERE name = 'AdCombo'),
 '[{"code": "US", "priority": 1}, {"code": "CA"}]'::jsonb, 10.00, 'USD', 'active', '{"token1": "value1"}'::jsonb, 'This is a demo offer 1', ARRAY['tag1', 'tag2']),
('Demo Offer 2', 'https://example.com/offer2',
 (SELECT id FROM affiliate_networks WHERE name = 'ClickDealer'),
 '[{"code": "UK", "priority": 1}, {"code": "AU"}]'::jsonb, 15.50, 'USD', 'active', '{"token2": "value2"}'::jsonb, 'This is a demo offer 2', ARRAY['tag3', 'tag4']);


-- Добавление демо-сетей
INSERT INTO affiliate_networks (name, offer_parameters, s2s_postback)
VALUES
('AdCombo', 'aff_id={aff_id}&subid={sub_id}', 'https://adcombo.com/postback?cid={clickid}&status={status}')
ON CONFLICT (name) DO NOTHING;

INSERT INTO affiliate_networks (name, offer_parameters, s2s_postback)
VALUES
('ClickDealer', 'aff_sub={subid}&click_id={cid}', 'https://clickdealer.com/pb?cid={cid}&conversion={conversion_status}')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    traffic_loss FLOAT,
    s2s_postback VARCHAR(1024),
    s2s_postback_statuses JSONB,        -- {"sale": true, "lead": false, ...}
    settings JSONB,                     -- массив из [{"name": ..., "parameter": ..., "token": ..., "editable_name": ...}]
    additional_settings JSONB,          -- taboola_api_key и др.
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

INSERT INTO sources (name, traffic_loss, s2s_postback, s2s_postback_statuses, settings, additional_settings)
VALUES
('Taboola US', 0.05, 'https://example.com/postback?clickid={clickid}',
 '{"sale": true, "lead": true, "reject": false, "upsell": false}',
 '[
  {"name": "Keyword", "parameter": "keyword", "token": "", "editable_name": false},
  {"name": "Cost", "parameter": "cost", "token": "", "editable_name": false},
  {"name": "Sub id 1", "parameter": "sub_id_1", "token": "", "editable_name": true},
  {"name": "Sub id 2", "parameter": "sub_id_2", "token": "", "editable_name": true}
 ]'::jsonb,
 '{
   "taboola_api_key": "taboola-us-key-123"
 }'::jsonb);

CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL
);

CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    alias VARCHAR(255) NOT NULL UNIQUE,
    type campaign_type DEFAULT 'campaign',
    status campaign_status DEFAULT 'active',
    redirect_mode redirect_mode DEFAULT 'position',
    domain_id INTEGER REFERENCES domains(id) ON DELETE SET NULL,
    traffic_source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    config JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Добавим начальные данные
INSERT INTO settings (name, value) VALUES
('settings', '{
  "domain": "",
  "currency": "USD",
  "timezone": "UTC",
  "autoUpdateReports": true,
  "apiToken": "a1b2c3d4e5f6",
  "enableLogging": false
}') ON CONFLICT (name) DO NOTHING;

INSERT INTO settings (name, value) VALUES
('subIdMapping', '[
  {"name":"Cost","parameter":"cost","token":"","editable_name":false},
  {"name":"Currency","parameter":"currency","token":"","editable_name":false},
  {"name":"External ID","parameter":"external_id","token":"","editable_name":false},
  {"name":"Creative ID","parameter":"utm_creative","token":"{{ad.name}}","editable_name":false},
  {"name":"AD Campaign ID","parameter":"utm_campaign","token":"{{campaign.name}}","editable_name":false},
  {"name":"Keyword","parameter":"keyword","token":"","editable_name":false},
  {"name":"Site","parameter":"utm_source","token":"{{site_source_name}}","editable_name":false},
  {"name":"Sub id 1","parameter":"sub_id_1","token":"","editable_name":true},
  {"name":"Sub id 2","parameter":"sub_id_2","token":"","editable_name":true},
  {"name":"Sub id 3","parameter":"sub_id_3","token":"","editable_name":true},
  {"name":"Sub id 4","parameter":"sub_id_4","token":"","editable_name":true},
  {"name":"Sub id 5","parameter":"sub_id_5","token":"","editable_name":true},
  {"name":"Sub id 6","parameter":"sub_id_6","token":"","editable_name":true},
  {"name":"Sub id 7","parameter":"sub_id_7","token":"","editable_name":true},
  {"name":"Sub id 8","parameter":"sub_id_8","token":"","editable_name":true},
  {"name":"Sub id 9","parameter":"sub_id_9","token":"","editable_name":true},
  {"name":"Sub id 10","parameter":"sub_id_10","token":"","editable_name":true}
]') ON CONFLICT (name) DO NOTHING;


-- Создание стартового пользователя tracker_admin
INSERT INTO users (username, email, password_hash, is_admin, active)
VALUES (
    'tracker_admin',
    'admin@example.com',
    '5dfc9a6ef90c0908795b917ae279e90a', /* akm_ + admin */
    TRUE,
    TRUE
);

INSERT INTO campaigns (
    name,alias, type, status, redirect_mode, domain_id, traffic_source_id, config, notes, created_at, updated_at
) VALUES (
    'Campaign Demo 1', 'alias1', 'campaign', 'active', 'position', 1, 1,
    '{"integration_method": "php", "send_se_referrer": true, "use_title_as_keyword": true, "send_query_params": true, "bind_method": "full", "bind_ttl_hours": 24, "cost_model": "cpc", "traffic_loss_percent": 0, "cost": 0, "cost_currency": "USD", "cost_from_cost_parameter": false, "paramsIdMapping": [{"name": "Keyword", "parameter": "keyword", "token": ""}, {"name": "Cost", "parameter": "cost", "token": ""}, {"name": "Currency", "parameter": "currency", "token": ""}, {"name": "External ID", "parameter": "external_id", "token": ""}, {"name": "Creative ID", "parameter": "utm_creative", "token": "{{ad.name}}"}, {"name": "AD Campaign ID", "parameter": "utm_campaign", "token": "{{campaign.name}}"}, {"name": "Site", "parameter": "utm_source", "token": "{{site_source_name}}"}], "postbacks": [], "flows": []}',
    'Demo notes for campaign 1', '2025-05-01 00:00:00', '2025-05-01 00:00:00'
);

INSERT INTO campaigns (
    name, alias, type, status, redirect_mode, domain_id, traffic_source_id, config, notes, created_at, updated_at
) VALUES (
    'Campaign Demo 2', 'alias2', 'campaign', 'active', 'position', 1, 1,
    '{"integration_method": "php", "send_se_referrer": true, "use_title_as_keyword": true, "send_query_params": true, "bind_method": "full", "bind_ttl_hours": 24, "cost_model": "cpc", "traffic_loss_percent": 0, "cost": 0, "cost_currency": "USD", "cost_from_cost_parameter": false, "paramsIdMapping": [{"name": "Keyword", "parameter": "keyword", "token": ""}, {"name": "Cost", "parameter": "cost", "token": ""}, {"name": "Currency", "parameter": "currency", "token": ""}, {"name": "External ID", "parameter": "external_id", "token": ""}, {"name": "Creative ID", "parameter": "utm_creative", "token": "{{ad.name}}"}, {"name": "AD Campaign ID", "parameter": "utm_campaign", "token": "{{campaign.name}}"}, {"name": "Site", "parameter": "utm_source", "token": "{{site_source_name}}"}], "postbacks": [], "flows": []}',
    'Demo notes for campaign 2', '2025-05-01 00:00:00', '2025-05-01 00:00:00'
);

INSERT INTO campaigns (
    name,alias,  type, status, redirect_mode, domain_id, traffic_source_id, config, notes, created_at, updated_at
) VALUES (
    'Campaign Demo 3', 'alias3', 'campaign', 'active', 'position', 1, 1,
    '{"integration_method": "php", "send_se_referrer": true, "use_title_as_keyword": true, "send_query_params": true, "bind_method": "full", "bind_ttl_hours": 24, "cost_model": "cpc", "traffic_loss_percent": 0, "cost": 0, "cost_currency": "USD", "cost_from_cost_parameter": false, "paramsIdMapping": [{"name": "Keyword", "parameter": "keyword", "token": ""}, {"name": "Cost", "parameter": "cost", "token": ""}, {"name": "Currency", "parameter": "currency", "token": ""}, {"name": "External ID", "parameter": "external_id", "token": ""}, {"name": "Creative ID", "parameter": "utm_creative", "token": "{{ad.name}}"}, {"name": "AD Campaign ID", "parameter": "utm_campaign", "token": "{{campaign.name}}"}, {"name": "Site", "parameter": "utm_source", "token": "{{site_source_name}}"}], "postbacks": [], "flows": []}',
    'Demo notes for campaign 3', '2025-05-01 00:00:00', '2025-05-01 00:00:00'
);