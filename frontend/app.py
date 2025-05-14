from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
import httpagentparser
from datetime import datetime
import asyncpg
from types import SimpleNamespace
import json
from fastapi.middleware.cors import CORSMiddleware
from user_agents import parse as parse_ua
import re
import os
import requests

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
        host="tracker_postgres",
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
from domains import router as domains_router

# Подключаем router
app.include_router(landings_router, tags=["Landings"])
app.include_router(domains_router, tags=["Domains"])

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


def show_landing(folder: str) -> Response:
    index_php = os.path.join("landings", folder, "index.php")
    index_html = os.path.join("landings", folder, "index.html")

    print(index_php, os.path.exists(index_php))
    if os.path.exists(index_php) or os.path.exists(index_html):
        url = f"https://tracker_nginx/l/{folder}"
        r = requests.get(url, verify=False)  # , data={"name": "Anton"})
        return Response(content=r.text, media_type="text/html")
    else:
        return Response(content="404 Not Found", status_code=404, media_type="text/html")


def do_redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=302)


async def get_default_campaign_from_db(domain: str):
    query = """
            select *
            from campaigns
            where id in (SELECT default_campaign_id
                         FROM domains
                         WHERE domain = $1
                         LIMIT 1); \
            """
    async with app.state.pg.acquire() as conn:
        row = await conn.fetchrow(query, domain)
        if row:
            return row
        return None


@app.get("/")
async def domain_page_default_campaign(request: Request) -> Response:
    host = request.headers.get("host")
    campaign = await get_default_campaign_from_db(host)

    if campaign is None:
        return Response(content="404 Not Found", media_type="text/html")

    # print('Requested campaign:', campaign)
    # print('Requested domain:', host)
    await track_event(campaign, request)
    return await do_campaign_execution(campaign, request)
    # return None


async def do_campaign_execution(campaign, request: Request) -> Response:
    log_track(f"🔁 New campaign execution call for '{campaign}'")

    # read campaign flow
    config = json.loads(campaign["config"])
    flow = config.get("flows", [])
    log_track(flow)

    return do_redirect('https://babber.app')

    return  show_landing('test')


async def track_event(campaign, request: Request):
    """ track events to ClickHouse """

    try:
        campaign_alias = campaign["alias"]
        log_track(f"🔁 New track data call for '{campaign_alias}'")
    except KeyError:
        msg = "❌ Campaign alias not found in track_event"
        log_track(msg)
        raise HTTPException(status_code=400, detail=msg)

    ch = request.app.state.ch

    content_type = request.headers.get('content-type', '')
    if content_type.startswith('application/x-www-form-urlencoded'):
        query = dict(await request.form())
    else:
        try:
            query = await request.json()
        except:
            query = {}

    config = json.loads(campaign["config"])

    # Извлекаем mapping из config.paramsIdMapping
    mapping = {}
    for item in config.get("paramsIdMapping", []):
        param = item.get("parameter")
        if param:
            mapping[param] = param

    # Стартовая запись
    result_row = {
        "campaign_id": str(campaign["id"])
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

    # TODO: POSTBACK SENDING ASYNC WITHOUT AWAIT
    try:
        columns = list(result_row.keys())
        values = [list(result_row.values())]
        ch.insert("clicks_data", values, column_names=columns)
        log_track(f"✅ Inserted into ClickHouse: {campaign_alias}")
    except Exception as e:
        log_track(f"❌ ClickHouse insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {e}")


@app.post("/pb")
def postback_receive():
    return {"status": "ok"}


# track and do campaign rules
@app.post("/{campaign_alias}")
async def post_with_campaign_alias(campaign_alias: str, request: Request):
    log_track(f"🔁 New post track request for '{campaign_alias}'")

    pg = request.app.state.pg

    # get campaign from db
    async with pg.acquire() as conn:
        campaign = await conn.fetchrow("""
                                       SELECT *
                                       FROM campaigns
                                       WHERE alias = $1
                                       """, campaign_alias)

    if not campaign:
        msg = f"❌ Campaign '{campaign_alias}' not found"
        log_track(msg)
        raise HTTPException(status_code=404, detail=msg)

    # tracking
    await track_event(campaign, request)

    await do_campaign_execution(campaign, request)

    return {"status": "ok", "campaign": campaign_alias}


@app.get("/_akm_tracker_debug")
def show_logs():
    return TRACK_LOG[-50:]  # последние 50 событий
