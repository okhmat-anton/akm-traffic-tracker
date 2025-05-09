from clickhouse_connect import get_client
from typing import List, Optional, Any


def get_clickhouse_client():
    return get_client(
        host='tracker_clickhouse',
        port=8123,
        username='user',
        password='password',
        database='default'
    )

def build_filters(
    filters: Optional[Any] = None,
    extra_clause: Optional[str] = None
) -> str:
    conditions = []

    if filters:
        if getattr(filters, 'date_from', None) and getattr(filters, 'date_to', None):
            conditions.append(
                f"received_at BETWEEN toDateTime('{filters.date_from}') AND toDateTime('{filters.date_to}')"
            )

        if getattr(filters, 'campaigns', None):
            ids = ','.join(map(str, filters.campaigns))
            conditions.append(f"campaign_id IN ({ids})")

    if extra_clause:
        clause = extra_clause.replace("WHERE", "").strip()
        if clause:
            conditions.append(clause)

    return f"WHERE {' AND '.join(conditions)}" if conditions else ""



def get_recent_visits(client, filters, limit: int = 100):
    where_clause = build_filters(filters)

    query = f"""
        SELECT ip, country, url, referrer, received_at
        FROM clicks
        {where_clause}
        ORDER BY received_at DESC
        LIMIT %(limit)s
    """

    print(query)
    result = client.query(query, parameters={'limit': limit})
    columns = result.column_names
    return [dict(zip(columns, row)) for row in result.result_rows]


def get_metrics_series(client, filters, limit: int = 30):
    where_clause = build_filters(filters)

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
        ORDER BY day DESC
        LIMIT %(limit)s
    """
    result = client.query(query, parameters={'limit': limit})
    columns = result.column_names
    rows = [dict(zip(columns, row)) for row in result.result_rows]
    return list(reversed(rows))
