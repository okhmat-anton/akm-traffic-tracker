from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import psycopg2
import os

from clickhouse_connect import get_client

app = FastAPI()

# Конфиг подключения к БД из переменных окружения
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'db'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'host': os.getenv('DB_HOST', 'localhost')
}

def save_event(event_type: str, css_selector: str):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clicks (event_type, css_selector) VALUES (%s, %s);",
        (event_type, css_selector)
    )
    conn.commit()
    cur.close()
    conn.close()


from landings import router as landings_router

# Подключаем router
app.include_router(landings_router, tags=["Landings"])


clickhouse = get_client(
    host='tracker_clickhouse',
    port=8123,
    username='user',
    password='password',
    database='default'
)

# CREATE TABLE IF NOT EXISTS clicks (
#     timestamp      DateTime,
#     campaign_alias String,
#     event_type     String,
#     visitor_id     String,
#     ip             String,
#     user_agent     String,
#     cost           Float64
# )
# ENGINE = MergeTree()
# ORDER BY (campaign_alias, timestamp);


def save_click_to_ch(data: dict):
    clickhouse.insert('clicks', [(
        data["timestamp"],
        data["campaign_alias"],
        data["event_type"],
        data["visitor_id"],
        data["ip"],
        data["user_agent"],
        float(data.get("cost", 0))
    )])

# Простой in-memory лог (замени на DB в бою)
TRACK_LOG = []

@app.post("/{campaign_alias}")
async def track_event(campaign_alias: str, request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    event_type = data.get("type")
    visitor_id = data.get("visitor_id")
    user_agent = data.get("user_agent")
    cost = data.get("cost", 0)

    if event_type not in ["visit", "lead", "sale", "reject", "upsale", "pending"]:
        return JSONResponse({"error": "Invalid event type"}, status_code=400)

    log_entry = {
        "timestamp": datetime.utcnow(),
        "campaign_alias": campaign_alias,
        "event_type": event_type,
        "visitor_id": visitor_id,
        "ip": request.client.host,
        "user_agent": user_agent,
        "cost": cost
    }

    save_click_to_ch(log_entry)

    print("Tracked:", log_entry)
    return {"status": "ok"}


@app.get("/_akm_tracker_debug")
def get_all_logs():
    return TRACK_LOG

