import random
import time as time_main
from datetime import datetime, timedelta, time, date
from clickhouse_connect import get_client

client = get_client(
    host='tracker_clickhouse',
    port=8123,
    username='user',
    password='password_password_password',
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
        'offer_id',
        'ad_campaign_id',
        'status',
        'external_id',
        'keyword',
        'landing_id',
        'language',
        'url',
        'referrer',
        'browser',
        'browser_version',
        'connection_type',
        'cost',
        'profit',
        'revenue',
        'country',
        'region',
        'city',
        'utm_creative','utm_source',
        'visitor_id',
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
        'user_agent',
        'traffic_source_name',
        'os',
        'isp',
        'ip',
        'is_using_proxy',
        'is_bot',
        'device_type',
        'device_brand'
    ]

def generate_timestamp(day):
    return datetime.combine(day, time(hour=random.randint(0, 23), minute=random.randint(0, 59)))


def generate_click_row(day):
    ts = datetime.combine(day, time(hour=random.randint(0, 23), minute=random.randint(0, 59)))
    cost = round(random.uniform(0.05, 0.5), 3)
    revenue = round(cost + random.uniform(0.3, 2.5), 3) if random.random() < 0.3 else None
    is_bot = random.random() < 0.05

    return [
        ts,  # received_at
        4,  # campaign_id
        random.randint(1, 2),  # offer_id
        f"ad_{random.randint(1000, 9999)}",  # ad_campaign_id
        random.choice(STATUSES),  # status
        f"ext_{random.randint(100000, 999999)}",  # external_id
        f"keyword_{random.randint(1, 100)}",  # keyword
        f"land_{random.randint(1, 50)}",  # landing_id
        random.choice(LANGUAGES),  # language
        f"https://{random.choice(DOMAINS)}",  # url
        "https://referrer.com",  # referrer
        random.choice(BROWSERS),  # browser
        str(random.randint(80, 120)),  # browser_version
        random.choice(["wifi", "4g", "ethernet"]),  # connection_type
        cost,  # cost
        round(cost * random.uniform(0.2, 0.5), 3) if revenue else None,  # profit
        revenue,  # revenue
        random.choice(COUNTRIES),  # country
        "RegionName",  # region
        "CityName",  # city
        f"cr_{random.randint(1, 100)}",  # utm_creative
        f"visitor_{random.randint(100000, 999999)}",  # visitor_id
        *[f"sub{i}_{random.randint(1, 100)}" for i in range(1, 11)],  # sub_id_1 to sub_id_10
        "Mozilla/5.0",  # user_agent
        "Google",  # traffic_source_name
        random.choice(OS),  # os
        random.choice(ISPS),  # isp
        f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}",  # ip
        random.choice([True, False, None]),  # is_using_proxy
        is_bot,  # is_bot
        random.choice(DEVICE_TYPES),  # device_type
        random.choice(DEVICES)  # device_brand
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
    client.insert('clicks_data', batch, column_names)
    time_main.sleep(5)


def seed_all():
    base_day = datetime.utcnow().date() - timedelta(days=40)
    for i in range(40):
        day = base_day + timedelta(days=i)
        count_clicks = random.randint(1000, 5000)
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
