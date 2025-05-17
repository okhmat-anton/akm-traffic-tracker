from fastapi import APIRouter, Request, HTTPException, Query
from clickHouse import get_recent_visits, get_metrics_series
from schemas import Filters

router = APIRouter()


@router.post("/visits")
async def get_visits(
        request: Request,
        filters: Filters
):
    try:
        ch = request.app.state.ch
        rows = get_recent_visits(ch, filters)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics")
async def get_metrics(request: Request, filters: Filters):
    ch = request.app.state.ch
    series = get_metrics_series(ch, filters)

    total_visits = sum(row['visits'] for row in series)
    total_unique_visits = sum(row['unique_visits'] for row in series)
    total_clicks = sum(row['clicks'] for row in series)
    total_unique_clicks = sum(row['unique_clicks'] for row in series)
    total_conversions = sum(row['conversions'] for row in series)
    total_cost = sum(row['cost'] or 0 for row in series)
    total_revenue = sum(row['revenue'] or 0 for row in series)
    roi = f"{round(((total_revenue - total_cost) / total_cost * 100), 2)}%" if total_cost else "—"

    return {
        "metrics": {
            "visits": total_visits,
            "unique_visits": total_unique_visits,
            "clicks": total_clicks,
            "unique_clicks": total_unique_clicks,
            "conversions": total_conversions,
            "cost": round(total_cost, 2),
            "revenue": round(total_revenue, 2),
            "roi": roi
        },
        "chart": {
            "labels": [str(row["day"]) for row in series],
            "visits": [row["visits"] for row in series],
            "unique_visits": [row["unique_visits"] for row in series],
            "clicks": [row["clicks"] for row in series],
            "conversions": [row["conversions"] for row in series],
            "unique_clicks": [row["unique_clicks"] for row in series]
        }
    }
