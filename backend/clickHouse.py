from datetime import datetime, timedelta, date
from clickhouse_connect import get_client
from typing import List, Optional, Any, Tuple, Dict, Union

from schemas import Filters


def get_clickhouse_client():
    return get_client(
        host='tracker_clickhouse',
        port=8123,
        username='user',
        password='password',
        database='default'
    )


def build_filters(filters: Union[dict, object]) -> Tuple[str, dict]:
    def get(val, default=None):
        if isinstance(filters, dict):
            return filters.get(val, default)
        return getattr(filters, val, default)

    conditions = []
    params = {}

    # Фильтр по дате
    date_from = get("date_from")
    date_to = get("date_to")
    if date_from and date_to:
        conditions.append("toDate(received_at) BETWEEN toDate(%(date_from)s) AND toDate(%(date_to)s)")
        params["date_from"] = date_from
        params["date_to"] = date_to

    # Фильтр по кампаниям
    campaigns = get("campaigns")
    if campaigns:
        conditions.append("campaign_id IN %(campaigns)s")
        params["campaigns"] = tuple(campaigns)

    # Дополнительные фильтры можно добавить здесь:
    # detail_level = get("detail_level")
    # if detail_level == "SomeLevel":
    #     conditions.append("...")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where_clause, params


def get_recent_visits(client, filters, limit: int = 100):
    where_clause, params = build_filters(filters)
    params['limit'] = limit

    query = f"""
        SELECT ip, country, url, referrer, received_at
        FROM clicks
        {where_clause}
        ORDER BY received_at DESC
        LIMIT %(limit)s
    """

    result = client.query(query, parameters=params)
    columns = result.column_names
    return [dict(zip(columns, row)) for row in result.result_rows]


def generate_date_range(start: str, end: str) -> List[str]:
    date_from = datetime.strptime(start, "%Y-%m-%d")
    date_to = datetime.strptime(end, "%Y-%m-%d")
    return [(date_from + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range((date_to - date_from).days + 1)]


def get_metrics_series(client, filters: Filters, limit: int = 30) -> List[Dict[str, Any]]:
    from datetime import date, timedelta

    print(filters)
    filters_dict = filters.dict()

    if not filters_dict.get("date_from") or not filters_dict.get("date_to"):
        end_date = date.today()
        start_date = end_date - timedelta(days=limit - 1)
        filters_dict["date_from"] = str(start_date)
        filters_dict["date_to"] = str(end_date)
    else:
        start_date = date.fromisoformat(filters_dict["date_from"])
        end_date = date.fromisoformat(filters_dict["date_to"])

    where_clause, params = build_filters(filters_dict)
    params["limit"] = limit

    query = f"""
        SELECT
            toDate(received_at) AS day,
            count(*) AS clicks,
            uniq(visitor_id) AS unique_clicks,
            countIf(status = 'conversion') AS conversions,
            sumOrNull(toFloat64(cost)) AS cost,
            sumOrNull(toFloat64(revenue)) AS revenue
        FROM clicks
        {where_clause}
        GROUP BY day
        ORDER BY day
    """

    print("QUERY:", query)

    try:
        result = client.query(query, parameters=params)
    except Exception as e:
        print("ClickHouse QUERY ERROR:", str(e))
        print("QUERY:", query)
        print("PARAMS:", params)
        raise

    # преобразуем результат в dict по дате
    columns = result.column_names
    raw_rows = [dict(zip(columns, row)) for row in result.result_rows]
    data_by_day = {row["day"]: row for row in raw_rows}

    # собираем все дни от start_date до end_date
    output = []
    current = start_date
    while current <= end_date:
        row = data_by_day.get(current, {
            "day": current,
            "clicks": 0,
            "unique_clicks": 0,
            "conversions": 0,
            "cost": 0.0,
            "revenue": 0.0
        })
        output.append(row)
        current += timedelta(days=1)

    return output
