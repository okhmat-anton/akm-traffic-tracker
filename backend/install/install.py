import psycopg2
import os
import shutil
import sys
from clickhouse_connect import get_client

DB_HOST = "tracker_postgres"
DB_PORT = "5432"
DB_NAME = "db"
DB_USER = "user"
DB_PASSWORD = "password_password_password"

INIT_SQL_FILE = "/app/install/sql/init.sql"


def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


conn = connect_db()


def check_and_reset_database():
    # return
    try:
        conn.autocommit = True
        cur = conn.cursor()

        # Проверка наличия таблиц
        cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public';
                    """)
        tables = cur.fetchall()

        if tables:
            print("\n⚠️  Найдены таблицы в базе данных:\n")
            for table in tables:
                print(f" - {table[0]}")
            confirm = input(
                "\n❓ Вы действительно хотите УДАЛИТЬ ВСЕ ТАБЛИЦЫ? Введите 'yes' для подтверждения: ").strip()

            if confirm.lower() == "yes":
                print("\n🗑️ Удаляем все таблицы...")
                for table in tables:
                    cur.execute(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE;')
                print("✅ Все таблицы успешно удалены.\n")
            else:
                print("\n❌ Операция отменена. База данных осталась без изменений.\n")
                sys.exit(1)

        else:
            print("ℹ️  В базе данных нет таблиц. Установка продолжается...\n")

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"\n🚫 Не удалось подключиться к базе данных: {e}\n")
        sys.exit(1)


def run_install():
    try:
        check_and_reset_database()
        # Подключение к базе
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Чтение init.sql
        with open(INIT_SQL_FILE, "r", encoding="utf-8") as f:
            sql_commands = f.read()

        # Выполнение всех команд
        cursor.execute(sql_commands)

        print("✅ Postgres база данных успешно инициализирована.")

        cursor.close()
        conn.close()

        run_clickhouse_install()

        print('\n✅ Установка завершена. Clickhouse База данных инициализирована.')

    except Exception as e:
        print(f"❌ Ошибка установки: {e}")


def run_clickhouse_install():
    print("Connecting to ClickHouse...")

    client = get_client(
        host=os.getenv("CLICKHOUSE_HOST", "tracker_clickhouse"),
        username=os.getenv("CLICKHOUSE_USER", "user"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "password_password_password"),
        port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
        secure=False
    )

    sql_file_path = os.path.join(os.path.dirname(__file__), 'sql/clickHouse.sql')
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        raw_sql = f.read()

    # Разбиваем по ; и удаляем пустые
    statements = [s.strip() for s in raw_sql.split(';') if s.strip()]

    for statement in statements:
        print(f"\nExecuting:\n{statement}")
        client.command(statement)

    print("\n✅ ClickHouse install complete.")


if __name__ == "__main__":
    run_install()
