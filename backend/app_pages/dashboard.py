from fastapi import APIRouter, Request, HTTPException
from clickHouse import get_recent_visits, get_metrics_series

router = APIRouter()

@router.get("/visits")
async def get_visits(request: Request):
    try:
        ch = request.app.state.ch  # клиент был создан в app.py
        rows = get_recent_visits(ch)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(request: Request):
    ch = request.app.state.ch
    series = get_metrics_series(ch)

    # Общие метрики по последним N дням
    total_clicks = sum(row['clicks'] for row in series)
    total_unique = sum(row['unique_clicks'] for row in series)
    total_conversions = sum(row['conversions'] for row in series)
    total_cost = sum(row['cost'] or 0 for row in series)
    total_revenue = sum(row['revenue'] or 0 for row in series)
    roi = f"{round(((total_revenue - total_cost) / total_cost * 100), 2)}%" if total_cost else "—"

    return {
        "metrics": {
            "clicks": total_clicks,
            "unique_clicks": total_unique,
            "conversions": total_conversions,
            "cost": round(total_cost, 2),
            "revenue": round(total_revenue, 2),
            "roi": roi
        },
        "chart": {
            "labels": [str(row["day"]) for row in series],
            "clicks": [row["clicks"] for row in series],
            "conversions": [row["conversions"] for row in series],
            "unique_clicks": [row["unique_clicks"] for row in series]
        }
    }