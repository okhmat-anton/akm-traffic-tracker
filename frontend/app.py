from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Optional
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import psycopg2
import os
import httpagentparser
from datetime import datetime
import asyncpg
from types import SimpleNamespace
import json
from fastapi.middleware.cors import CORSMiddleware
from user_agents import parse as parse_ua
import re
import socket
import subprocess
from pydantic import BaseModel
from pathlib import Path

from clickhouse_connect import get_client

app = FastAPI()
app.state = SimpleNamespace()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🚀 Startup
@app.on_event("startup")
async def startup():
    app.state.pg = await asyncpg.create_pool(
        user="user",
        password="password_password_password",
        database="db",
        host="postgres",
        port=5432
    )
    app.state.ch = get_client(
        host='tracker_clickhouse',
        port=8123,
        username='user',
        password='password_password_password',
        database='default'
    )


# 🛑 Shutdown
@app.on_event("shutdown")
async def shutdown():
    await app.state.pg.close()


VALID_PARAMS = [
    'ad_campaign_id', 'browser', 'campaign_id', 'city', 'connection_type', 'currency',
    'cost', 'country', 'utm_creative', 'utm_campaign', 'utm_source', 'device_brand', 'device_type', 'external_id', 'ip',
    'is_bot', 'is_using_proxy', 'isp', 'keyword', 'landing_id', 'language', 'offer_id',
    'os', 'profit', 'referrer', 'region', 'revenue', 'status', 'sub_id_1', 'sub_id_2', 'sub_id_3',
    'sub_id_4', 'sub_id_5', 'sub_id_6', 'sub_id_7', 'sub_id_8', 'sub_id_9', 'sub_id_10',
    'traffic_source_name', 'url', 'visitor_id'
]


from landings import router as landings_router

# Подключаем router
app.include_router(landings_router, tags=["Landings"])

##### main tracker app #####


# in-memory log
TRACK_LOG = []


def log_track(message: str):
    TRACK_LOG.append(message)
    if len(TRACK_LOG) > 50:
        TRACK_LOG.pop(0)


def enrich_meta(request: Request) -> dict:
    ua_string = request.headers.get('user-agent', '') or ''
    parsed = httpagentparser.detect(ua_string)
    ua = parse_ua(ua_string)

    language = request.headers.get('accept-language', '')
    country_code = None
    if language:
        # Пример: 'en-US,en;q=0.9' → 'US'
        match = re.search(r'-([A-Z]{2})', language)
        if match:
            country_code = match.group(1)

    return {
        'received_at': datetime.utcnow(),
        'ip': request.client.host,
        'referrer': request.headers.get('referer'),
        'current_domain': request.headers.get('host'),
        'language': request.headers.get('accept-language'),
        'country': country_code,
        'browser': parsed.get('browser', {}).get('name'),
        'os': parsed.get('os', {}).get('name'),
        'device_type': 'mobile' if 'Mobile' in ua_string else 'desktop',
        'is_bot': ua.is_bot or 'bot' in ua_string.lower(),
    }


@app.post("/{campaign_alias}")
async def track_event(campaign_alias: str, request: Request):
    log_track(f"🔁 New request for '{campaign_alias}'")

    pg = request.app.state.pg
    ch = request.app.state.ch

    content_type = request.headers.get('content-type', '')
    if content_type.startswith('application/x-www-form-urlencoded'):
        query = dict(await request.form())
    else:
        try:
            query = await request.json()
        except:
            query = {}

    # Получаем кампанию
    async with pg.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT *
            FROM campaigns
            WHERE alias = $1
        """, campaign_alias)

    if not row:
        msg = f"❌ Campaign '{campaign_alias}' not found"
        log_track(msg)
        raise HTTPException(status_code=404, detail=msg)

    campaign_id = row["id"]
    config = json.loads(row["config"])

    # Извлекаем mapping из config.paramsIdMapping
    mapping = {}
    for item in config.get("paramsIdMapping", []):
        param = item.get("parameter")
        if param:
            mapping[param] = param

    # Стартовая запись
    result_row = {
        "campaign_id": str(campaign_id),
        # "campaign_alias": campaign_alias
    }

    # Добавляем обогащённые поля
    meta = enrich_meta(request)
    for k, v in meta.items():
        if k in VALID_PARAMS:
            result_row[k] = v

    # Применяем mapping и добавляем параметры запроса
    for key in VALID_PARAMS:
        if key in query:
            mapped_key = mapping.get(key, key)
            result_row[mapped_key] = query[key]

    # ❗ Удаляем все поля со значением None
    result_row = {k: v for k, v in result_row.items() if v is not None}

    # Вставка в ClickHouse
    try:
        columns = list(result_row.keys())
        values = [list(result_row.values())]
        ch.insert("clicks_data", values, column_names=columns)
        log_track(f"✅ Inserted into ClickHouse: {campaign_alias}")
    except Exception as e:
        log_track(f"❌ ClickHouse insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {e}")

    return {"status": "ok", "campaign": campaign_alias}


@app.get("/_akm_tracker_debug")
def show_logs():
    return TRACK_LOG[-50:]  # последние 50 событий


################ DOMAINS API ####################

@app.get("/domain_ping", response_class=PlainTextResponse)
def ping():
    return "OK"


@app.post("/domain_update_nginx_and_ssl")
async def create_nginx(request: Request, domain_id: int):
    pg = request.app.state.pg

    async with pg.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT domain
            FROM domains
            WHERE id = $1
        """, domain_id)

    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain = row["domain"]
    path = generate_nginx_conf(domain, domain_id)
    return {"status": "ok", "file": str(path)}


def generate_nginx_conf(domain: str, domain_id: int) -> Path:
    template_path = Path("../nginx/nginx.prod.conf")
    output_dir = Path("../nginx/domains")

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Читаем шаблон
    content = template_path.read_text()

    # Заменяем плейсхолдер
    updated = content.replace("yourdomain.com", domain)

    # Создаём целевой путь
    output_dir.mkdir(parents=True, exist_ok=True)
    target_path = output_dir / f"{domain}_{domain_id}.conf"

    # Записываем результат
    target_path.write_text(updated)
    print(f"✅ Сконфигурирован: {target_path}")

    return target_path
