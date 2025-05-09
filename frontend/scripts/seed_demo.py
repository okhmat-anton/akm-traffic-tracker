import random
from datetime import datetime, timedelta, time, date
from clickhouse_connect import get_client

client = get_client(
    host='tracker_clickhouse',
    port=8123,
    username='user',
    password='password',
    database='default'
)

STATUSES = ['visit', 'conversion', 'rejected']
BROWSERS = ['Chrome', 'Firefox', 'Safari', 'Edge']
OS = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
COUNTRIES = ['US', 'UA', 'DE', 'PL', 'FR', 'IN']
DOMAINS = ['example.com', 'demo.site']
LANGUAGES = ['en-US', 'uk-UA', 'de-DE', 'fr-FR']
ISPS = ['Comcast', 'AT&T', 'Vodafone', 'Kyivstar']
DEVICE_TYPES = ['desktop', 'mobile', 'tablet']
DEVICES = ['Apple', 'Samsung', 'Xiaomi', 'Lenovo']

column_names = [
        'received_at',
        'campaign_id',
        'ad_campaign_id',
        'affiliate_network_name',
        'browser',
        'browser_version',
        'connection_type',
        'city',
        'campaign_name',
        'campaign_alias',
        'conversion_cost',
        'conversion_profit',
        'conversion_revenue',
        'conversion_sale_time',
        'conversion_time',
        'cost',
        'country',
        'creative_id',
        'visitor_id',
        'token',
        'tid',
        'subid',
        'sub_id_1',
        'sub_id_2',
        'sub_id_3',
        'sub_id_4',
        'sub_id_5',
        'sub_id_6',
        'sub_id_7',
        'sub_id_8',
        'sub_id_9',
        'sub_id_10',
        'visitor_code',
        'user_agent',
        'ts_id',
        'traffic_source_name',
        'x_requested_with',
        'stream_id',
        'status',
        'source',
        'search_engine',
        'sample',
        'revenue',
        'parent_campaign_id',
        'previous_status',
        'profit',
        'url',
        'referrer',
        'region',
        'os_version',
        'os',
        'original_status',
        'operator',
        'offer_value',
        'keyword',
        'landing_id',
        'language',
        'offer',
        'offer_id',
        'offer_name',
        'isp',
        'is_using_proxy',
        'ip',
        'is_bot',
        'from_file',
        'external_id',
        'device_type',
        'current_domain',
        'date',
        'debug',
        'destination',
        'device_brand'
    ]

def generate_timestamp(day):
    return datetime.combine(day, time(hour=random.randint(0, 23), minute=random.randint(0, 59)))


def generate_click_row(day):
    ts = generate_timestamp(day)
    cost = round(random.uniform(0.05, 0.5), 3)
    revenue = round(cost + random.uniform(0.3, 2.5), 3) if random.random() < 0.3 else None
    is_bot = random.random() < 0.05

    return [
        ts,  # received_at
        '4',  # campaign_id
        f"ad_{random.randint(1000, 9999)}",  # ad_campaign_id
        'networkA',  # affiliate_network_name
        random.choice(BROWSERS),  # browser
        str(random.randint(80, 120)),  # browser_version
        'wifi',  # connection_type
        'Kyiv',  # city
        'Campaign test',  # campaign_name
        'alias_abc',  # campaign_alias
        None, None, revenue, None,  # conversion_cost, conversion_profit, conversion_revenue, conversion_sale_time
        None,  # conversion_time
        cost,  # cost
        random.choice(COUNTRIES),  # country
        f"cr_{random.randint(1, 100)}",  # creative_id
        f"uid_{random.randint(1, 1_000_000)}",  # visitor_id
        '', '', '', '', '', '', '', '', '', '', '', '', '',  # token, tid, subid, sub_id_1-10
        '',  # visitor_code
        'Mozilla/5.0',  # user_agent
        '',  # ts_id
        'Google',  # traffic_source_name
        '',  # x_requested_with
        '',  # stream_id
        random.choice(STATUSES),  # status
        'bing',  # source
        'google',  # search_engine
        '',  # sample
        revenue,  # revenue
        '',  # parent_campaign_id
        '',  # previous_status
        None,  # profit
        f"https://{random.choice(DOMAINS)}",  # url
        'https://facebook.com',  # referrer
        'Kyiv region',  # region
        '10.15',  # os_version
        random.choice(OS),  # os
        '',  # original_status
        'lifecell',  # operator
        '', '', '',  # offer_value, keyword, landing_id
        random.choice(LANGUAGES),  # language
        '', '', '',  # offer, offer_id, offer_name
        random.choice(ISPS),  # isp
        random.choice([True, False, None]),  # is_using_proxy
        f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}",  # ip
        is_bot,  # is_bot
        '',  # from_file
        '',  # external_id
        random.choice(DEVICE_TYPES),  # device_type
        random.choice(DOMAINS),  # current_domain
        ts.date(),  # date
        None,  # debug
        '',  # destination
        random.choice(DEVICES),  # device_brand
    ]


def seed_day(day: date, count: int = 1000):
    print(f"→ Generating {count} rows for {day}")
    batch = [generate_click_row(day) for _ in range(count)]

    row = generate_click_row(day)
    if len(row) != len(column_names):
        print(f"❌ Mismatch: row has {len(row)}, expected {len(column_names)}")
        for i, (col, val) in enumerate(zip(column_names, row)):
            print(f"{i + 1:02d}. {col}: {repr(val)}")
        raise SystemExit("❌ Fix your generate_click_row to match columns.")
    client.insert('clicks', batch, column_names)


def seed_all():
    base_day = datetime.utcnow().date() - timedelta(days=19)
    for i in range(60):
        day = base_day + timedelta(days=i)
        count_clicks = random.randint(100000, 200000)
        seed_day(day, count_clicks)


def debug_column_alignment():
    print("🔍 Проверка соответствия колонок...")
    test_row = generate_click_row(datetime.utcnow().date())
    if len(test_row) != len(column_names):
        print(f"❌ Длина не совпадает: row={len(test_row)}, columns={len(column_names)}")

        # Найти какие поля отсутствуют
        missing = []
        for i in range(len(column_names)):
            if i >= len(test_row):
                missing.append((i + 1, column_names[i]))

        if missing:
            print("\n❗ Отсутствуют значения для колонок:")
            for idx, col in missing:
                print(f"  {idx:02d}. {col}")

        # Если есть лишние значения
        if len(test_row) > len(column_names):
            print("\n⚠️ Лишние значения в row:")
            for i in range(len(column_names), len(test_row)):
                print(f"  {i + 1:02d}. {test_row[i]}")

    else:
        print("✅ Количество колонок совпадает.")

    # Вывести соответствие значений
    print("\n📋 Сопоставление колонка <-> значение:")
    for i, (col, val) in enumerate(zip(column_names, test_row)):
        print(f"{i + 1:02d}. {col:25} => {repr(val)}")


if __name__ == "__main__":
    # debug_column_alignment()
    print("🚀 Seeding demo data into ClickHouse...")
    seed_all()
    print("✅ Done.")
