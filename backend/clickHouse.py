from clickhouse_connect import get_client
from typing import List, Dict

def get_clickhouse_client():
    return get_client(
        host='tracker_clickhouse',
        port=8123,
        username='user',
        password='password',
        database='default'
    )

def get_recent_visits(client, limit: int = 50) -> List[Dict]:
    query = """
        SELECT ip, country, region, city, user_agent, url, referrer, received_at
        FROM clicks
        ORDER BY received_at DESC
        LIMIT %(limit)s
    """
    result = client.query(query, parameters={'limit': limit})
    columns = result.column_names
    return [dict(zip(columns, row)) for row in result.result_rows]


def get_metrics_series(client, limit: int = 30):
    query = """
        SELECT
            toDate(received_at) AS day,
            count(*) AS clicks,
            uniq(visitor_id) AS unique_clicks,
            countIf(status = 'conversion') AS conversions,
            sumOrNull(toFloat64(cost)) AS cost,
            sumOrNull(toFloat64(revenue)) AS revenue
        FROM clicks
        GROUP BY day
        ORDER BY day DESC
        LIMIT %(limit)s
    """
    result = client.query(query, parameters={'limit': limit})
    columns = result.column_names
    rows = [dict(zip(columns, row)) for row in result.result_rows]
    return list(reversed(rows))  # чтобы дни шли по возрастанию
