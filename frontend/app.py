import random

from fastapi import FastAPI, Request, HTTPException, Response, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
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
import httpx

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path

from clickhouse_connect import get_client
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import uuid

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
    'cost', 'country', 'utm_creative', 'utm_campaign', 'utm_source', 'device_type', 'external_id', 'ip',
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


async def enrich_meta(request: Request, params_id_mapping: list = None) -> dict:
    ua_string = request.headers.get('user-agent', '') or ''
    parsed = httpagentparser.detect(ua_string)
    ua = parse_ua(ua_string)

    language = request.headers.get('accept-language', '')
    country_code = None
    if language:
        match = re.search(r'-([A-Z]{2})', language)
        if match:
            country_code = match.group(1)

    # Параметры GET
    query_params = dict(request.query_params)

    # Параметры POST
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            post_data = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            post_data = dict(await request.form())
        else:
            post_data = {}
    except Exception:
        post_data = {}

    # Cookies
    cookies = request.cookies

    # Собираем всё в один плоский словарь
    meta = {
        "received_at": datetime.utcnow().isoformat(),
        "ip": request.client.host,
        "referrer": request.headers.get("referer"),
        "current_domain": request.headers.get("host"),
        "language": language,
        "country": country_code,
        "browser": parsed.get("browser", {}).get("name"),
        "os": parsed.get("os", {}).get("name"),
        "device_type": "mobile" if "Mobile" in ua_string else "desktop",
        "is_bot": ua.is_bot or "bot" in ua_string.lower(),
        "user_agent": ua_string,
    }

    combined = {**query_params, **post_data, **cookies}

    # Добавляем query, post, cookie параметры напрямую
    for k, v in combined.items():
        if k not in meta:  # не перезаписываем базовые ключи
            meta[k] = v

    log_track('params_id_mapping')
    log_track(params_id_mapping)

    if params_id_mapping:
        for param in params_id_mapping:
            param_key = param.get("parameter")  # например: sub_id_2
            token_key = param.get("token", "").strip()  # например: var_in

            if not param_key:
                continue

            # Если токен есть и он пришёл в запросе
            if token_key and token_key in combined:
                value = combined[token_key]
                meta[token_key] = value
                meta[param_key] = value
            # Если токена нет — пробуем по параметру напрямую
            elif param_key in combined:
                meta[param_key] = combined[param_key]

    return meta


async def show_landing(folder: str, offer_url: str = None) -> Response:
    index_php = os.path.join("landings", folder, "index.php")
    index_html = os.path.join("landings", folder, "index.html")

    print(index_php, os.path.exists(index_php))
    if os.path.exists(index_php) or os.path.exists(index_html):
        url = f"https://tracker_nginx/l/{folder}"
        r = requests.get(url, verify=False)  # , data={"name": "Anton"})
        html = r.text
        if offer_url:
            html = html.replace("{offer}", offer_url)
        return Response(content=html, media_type="text/html")
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


def render_404_html() -> Response:
    path = Path("static/404.html")
    if path.exists():
        html = path.read_text(encoding="utf-8")
    else:
        html = "<h1>404 Not Found</h1>"
    return Response(content=html, status_code=404, media_type="text/html")


def generate_click_id():
    return str(uuid.uuid4())


@app.get("/c/{campaign_alias}/{offer_id}")
async def campaign_click(
        campaign_alias: str,
        offer_id: str,
        request: Request,
        background_tasks: BackgroundTasks
) -> Response:
    log_track(f"🔁 New campaign click request {campaign_alias} - {offer_id}")
    pg = request.app.state.pg

    async with pg.acquire() as conn:
        # 1. Кампания
        campaign = await conn.fetchrow("SELECT * FROM campaigns WHERE alias = $1", campaign_alias)
        if not campaign:
            log_track(f"❌ CAMPAIGN NOT FOUND request {campaign_alias} - {offer_id}")

        # 2. Оффер
        offer = await conn.fetchrow("SELECT * FROM offers WHERE id = $1", int(offer_id))
        if not offer:
            return Response("Offer not found", status_code=404)

    # 4. Обогащение meta-данных через paramsIdMapping
    paramsIdMapping = get_params_id_mapping_from_campaign(campaign)
    meta_data = await enrich_meta(request, paramsIdMapping)

    # Обязательные поля
    meta_data["campaign_id"] = campaign["id"]
    meta_data["offer_id"] = offer["id"]
    landing_id = request.query_params.get("l_id")
    if landing_id:
        meta_data["landing_id"] = offer["id"]
    meta_data["click_id"] = meta_data.get("click_id") or generate_click_id()

    # 5. Асинхронное сохранение клика
    background_tasks.add_task(save_click_to_db, meta_data)

    # 6. Генерация финального URL
    offer_url = offer["url"]
    for key, value in meta_data.items():
        placeholder = f"{{{key}}}"
        if placeholder in offer_url:
            offer_url = offer_url.replace(placeholder, str(value))

    # 2. Обязательное добавление click_id как ?click_id=...
    parsed = urlparse(offer_url)
    query_params = dict(parse_qsl(parsed.query))
    query_params["click_id"] = meta_data["click_id"]  # обязательно

    # Сборка финального URL
    offer_url = urlunparse(parsed._replace(query=urlencode(query_params)))

    return RedirectResponse(offer_url)


async def save_click_to_db(meta: dict):
    pg = app.state.pg

    # допустимые поля из структуры таблицы conversions_data
    allowed_fields = {
        "click_id", "campaign_id", "offer_id", "landing_id", "ad_campaign_id",
        "status", "external_id", "payout", "revenue", "profit", "currency",
        "transaction_id", "country", "region", "city", "ip", "visitor_id",
        "sub_id_1", "sub_id_2", "sub_id_3", "sub_id_4", "sub_id_5",
        "sub_id_6", "sub_id_7", "sub_id_8", "sub_id_9", "sub_id_10",
        "utm_campaign", "utm_creative", "utm_source", "traffic_source_name",
        "os", "isp", "is_using_proxy", "is_bot", "device_type"
    }

    # фильтруем только допустимые поля
    insert_data = {k: v for k, v in meta.items() if k in allowed_fields}

    insert_data["received_at"] = datetime.utcnow()

    insert_data["status"] = 'lead'

    columns = ", ".join(insert_data.keys())
    values_placeholders = ", ".join(
        ["NOW()" if v == "now()" else f"${i + 1}" for i, v in enumerate(insert_data.values())]
    )
    values = [v for v in insert_data.values() if v != "now()"]

    query = f"INSERT INTO conversions_data ({columns}) VALUES ({values_placeholders})"

    async with pg.acquire() as conn:
        await conn.execute(query, *values)


@app.get("/pb/{click_id}/{status}/{payout}")
async def postback_receive(click_id: str, status: str, payout: str, request: Request,
                           background_tasks: BackgroundTasks):
    VALID_STATUSES = {"lead", "sale", "upsale", "rejected", "hold", "trash"}

    # update status in db but only 'lead', 'sale', 'upsale', 'rejected', 'hold', 'trash'
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    try:
        payout_value = float(payout)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payout format")

    pg = request.app.state.pg

    async with pg.acquire() as conn:
        result = await conn.execute("""
                                    UPDATE conversions_data
                                    SET status = $1, payout = $2
                                    WHERE click_id = $3
                                    """, status, payout_value, click_id)

        # try:
        if True:
            # запросить компанию по click_id
            row = await conn.fetchrow("""
                                      SELECT *
                                      FROM conversions_data
                                          JOIN campaigns c on conversions_data.campaign_id = c.id
                                      WHERE click_id = $1
                                      """, click_id)

            # log_track(f'postbacks row {click_id}')
            # log_track(row)
            if row and row["config"]:
                config = json.loads(row["config"])
                # cycle of postbacks
                postbacks = config.get("postbacks", [])
                # log_track('postbacks')
                # log_track(postbacks)

                offer_id = row["offer_id"]
                # get offer from db
                offer = await conn.fetchrow("SELECT * FROM offers WHERE id = $1", offer_id)
                if offer:
                    we_pay__payout_value = offer["payout"]

                for postback in postbacks:
                    url = postback.get("url")
                    if url:

                        # send postback
                        data = {
                            "click_id": click_id,
                            "status": status,
                            "payout": we_pay__payout_value
                        }
                        # если row — asyncpg.Record → преобразуем в dict и мержим
                        if row:
                            data.update(dict(row))
                        post_type = postback.get("method") == "POST"
                        log_track(f"<UNK> Postback Type: {post_type}")
                        # await send_postback(url, data, post_type)
                        background_tasks.add_task(send_postback, url, data, post=True)

        # except:
        #     log_track(f"<UNK> CAMPAIGN NOT FOUND request {click_id}")
        #     # log error
        #     raise HTTPException(status_code=404, detail="Click ID not found")

    return JSONResponse(content={"status": "ok", "click_id": click_id, "updated_status": status})


@app.get("/")
async def domain_page_default_campaign(request: Request) -> Response:
    log_track('🔁 Domain request')
    host = request.headers.get("host")
    campaign = await get_default_campaign_from_db(host)

    if campaign is None:
        return Response(content="404 Not Found", media_type="text/html")

    # print('Requested campaign:', campaign)
    # print('Requested domain:', host)
    await track_event(campaign, request)
    return await do_campaign_execution(campaign, request)
    # return None


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in (404, 405):
        host = request.headers.get("host", "").lower().strip()
        if host:
            pg = app.state.pg
            async with pg.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM domains WHERE domain = $1", host)
                log_track(f"🔁 domain '{row}'")
                if row and row['handle_404'] == 'handle':
                    log_track('HANDLE 404')
                    return await domain_page_default_campaign(request)

        return render_404_html()
    # other errors by default
    return Response(content=str(exc.detail), status_code=exc.status_code)


def check_filters(meta: dict, filters: list, request: Request) -> bool:
    result = None

    for idx, f in enumerate(filters):
        key = f.get("key")
        op = f.get("operator")
        val = str(f.get("value", "")).strip()
        condition = f.get("condition", "").lower()

        ctx_val = str(meta.get(key, "")).strip()

        match op:
            case "equals":
                passed = ctx_val == val
            case "not_equals":
                passed = ctx_val != val
            case "contains":
                passed = val in ctx_val
            case "not_contains":
                passed = val not in ctx_val
            case "starts_with":
                passed = ctx_val.startswith(val)
            case "ends_with":
                passed = ctx_val.endswith(val)
            case "greater":
                try:
                    passed = float(ctx_val) > float(val)
                except:
                    passed = False
            case "less":
                try:
                    passed = float(ctx_val) < float(val)
                except:
                    passed = False
            case "in":
                passed = ctx_val in val.split(",")
            case "not_in":
                passed = ctx_val not in val.split(",")
            case _:
                passed = False

        if idx == 0 or condition == "":
            result = passed
        elif condition == "and":
            result = result and passed
        elif condition == "or":
            result = result or passed

    return bool(result)


def get_params_id_mapping_from_campaign(campaign: dict) -> list:
    config_str = campaign.get("config")
    if not config_str:
        return []

    try:
        config = json.loads(config_str)
        return config.get("paramsIdMapping", [])
    except json.JSONDecodeError:
        return []


async def do_campaign_execution(campaign, request: Request) -> Response:
    log_track(f"🔁 New campaign execution call for '{campaign}'")

    config = json.loads(campaign["config"])
    flows = config.get("flows", [])
    # log_track(flows)

    pg = app.state.pg

    # FORCED FLOWS FIRST
    sorted_flows = sorted(
        flows,
        key=lambda f: (
            0 if f.get("type") == "forced" else 1,  # forced сначала
            f.get("position", 9999)  # потом по position
        )
    )

    # log_track('ALL FLOWS SORTED')
    # log_track(sorted_flows)

    paramsIdMapping = get_params_id_mapping_from_campaign(campaign)
    meta_data = await enrich_meta(request, paramsIdMapping)
    # log_track('META DATA')
    # log_track(meta_data)

    for flow in sorted_flows:
        if not flow.get("enabled"):
            continue

        # log_track('FLOW')
        # log_track(flow)
        if not flow:
            raise HTTPException(status_code=404, detail="No active flow")

        filters = flow.get("filters", [])
        if filters and not check_filters(meta_data, filters, request):
            # log_track(f"❌ Filters not passed: {filters}")
            continue

        schema = flow.get("schema")

        # log_track('SCHEMA')
        # log_track(schema)

        # SCHEMA: direct
        if schema == "direct":
            offer_url = get_real_offer_url(flow.get("offer"))
            # TODO: save_click_to_db
            # await save_click_info(flow.get("campaign_id"), flow.get("offer"), request)
            return RedirectResponse(offer_url)


        # SCHEMA: landing → offer
        elif schema == "landing_offer":
            landing = flow.get("landing")
            offer_id = flow.get("offer")
            if landing:
                async with pg.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM landings WHERE id = $1", landing)
                    if row:
                        landing_folder = row["folder"]
                        offer_url = await get_offer_click_url(campaign['alias'], offer_id, row['id'], meta_data)
                        return await show_landing(landing_folder, offer_url)
            return render_404_html()

        # SCHEMA: landing only
        elif schema == "landing_only":
            landing = flow.get("landing")
            if landing:
                async with pg.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM landings WHERE id = $1", landing)
                    if row:
                        landing_folder = row["folder"]
                        return await show_landing(landing_folder)
            return render_404_html()

        # SCHEMA: multi
        elif schema == "multi":
            # Pick random landing and offer
            landing_id = random.choice(flow.get("landings", []))
            offer_id = random.choice(flow.get("offers", []))

            if landing_id:
                async with pg.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM landings WHERE id = $1", landing_id)
                    if row:
                        landing_folder = row["folder"]
                        offer_url = await get_offer_click_url(campaign['alias'], offer_id, row['id'], meta_data)
                        return await show_landing(landing_folder, offer_url)
            return render_404_html()

        # SCHEMA: redirect
        elif schema == "redirect":
            # log_track(flow.get("redirect_url"))
            # TODO: save_click_to_db
            return RedirectResponse(flow.get("redirect_url"))

        # SCHEMA: redirect_campaign ++++
        elif schema == "redirect_campaign":
            campaign_id = flow.get("redirect_campaign")

            if campaign_id:
                async with pg.acquire() as conn:
                    campaign = await conn.fetchrow("SELECT * FROM campaigns WHERE id = $1", campaign_id)
                    # log_track(f"🔁 campaign for redirect - '{campaign}'")
                    if campaign:
                        return await do_campaign_execution(campaign, request)
            return render_404_html()
            # return RedirectResponse(flow.get("redirect_campaign"))

        # SCHEMA: return_404 +++
        elif schema == "return_404":
            return render_404_html()

    # Default fallback
    return render_404_html()


async def get_offer_click_url(campaign_alias: str, offer_id: str, landing_id: str = None,
                              offer_vars: dict = None) -> str:
    base_url = f"/c/{campaign_alias}/{offer_id}"
    query_params = {}

    if landing_id:
        query_params["l_id"] = landing_id

    if offer_vars:
        query_params.update(offer_vars)

    if query_params:
        return f"{base_url}?" + urlencode(query_params)

    return base_url


async def get_real_offer_url(offer_id: str, offer_vars: list = None) -> str:
    pg = app.state.pg
    async with pg.acquire() as conn:
        offer_row = await conn.fetchrow("SELECT * FROM offers WHERE id = $1", offer_id)
        # log_track(f"🔁 offer_row - '{offer_row}'")
        try:
            if offer_row:
                offer_url = offer_row["url"]
                if offer_vars:
                    for var in offer_vars:
                        offer_url = offer_url.replace(f"{{{var}}}", str(offer_row.get(var, "")))

                # log_track(f"🔁 offer_url - '{offer_url}'")
                return offer_url
        except TypeError:
            log_track(f"❌ TypeError Offer Url Build: {offer_row}")
    return ""


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
    meta_data = await enrich_meta(request, campaign.get("paramsIdMapping"))
    for k, v in meta_data.items():
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
        # log_track(f"✅ Inserted into ClickHouse: {campaign_alias}")
    except Exception as e:
        log_track(f"❌ ClickHouse insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {e}")


async def send_postback(url: str, data: dict, post: bool = False):
    VALID_PARAMS = [
        'payout', 'status', 'click_id', 'browser', 'campaign_id', 'city', 'connection_type', 'currency',
        'cost', 'country', 'utm_creative', 'utm_campaign', 'utm_source', 'device_type', 'external_id', 'ip',
        'is_bot', 'is_using_proxy', 'isp', 'keyword', 'landing_id', 'language', 'offer_id',
        'os', 'profit', 'referrer', 'region', 'revenue', 'status', 'sub_id_1', 'sub_id_2', 'sub_id_3',
        'sub_id_4', 'sub_id_5', 'sub_id_6', 'sub_id_7', 'sub_id_8', 'sub_id_9', 'sub_id_10',
        'traffic_source_name', 'url', 'visitor_id'
    ]

    # 🔒 Отфильтрованные параметры
    safe_data = {k: str(v) for k, v in data.items() if k in VALID_PARAMS}

    filled_url = url.format(**{k: str(v) for k, v in data.items()})

    log_track(f"<UNK> Sending Postback: {filled_url}")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if post:
                response = await client.post(filled_url, json=safe_data)
            else:
                response = await client.get(filled_url, params=safe_data)

        if response.status_code != 200:
            log_track(f"❌ Postback failed: {response.status_code} - {response.text}")

    except Exception as e:
        log_track(f"❌ Postback error: {str(e)}")


# track and do campaign rules
@app.get("/{campaign_alias}")
async def get_with_campaign_alias(campaign_alias: str, request: Request):
    log_track(f"🔁 New get track or compaign request for '{campaign_alias}'")

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
    return await do_campaign_execution(campaign, request)



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
    return JSONResponse(content=jsonable_encoder(TRACK_LOG[-50:]))
