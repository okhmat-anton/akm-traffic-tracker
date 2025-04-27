from fastapi import FastAPI, Request
import psycopg2
import os

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

@app.get("/")
async def root():
    return {"message": "Tracker API is working."}

@app.post("/track")
async def track_event(request: Request):
    data = await request.json()
    event_type = data.get("event_type")
    css_selector = data.get("css_selector")

    if not event_type or not css_selector:
        return {"error": "Missing event_type or css_selector"}, 400

    save_event(event_type, css_selector)
    return {"status": "ok"}
