import psycopg2

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "db"
DB_USER = "user"
DB_PASSWORD = "password"

INIT_SQL_FILE = "sql/init.sql"


def run_install():
    try:
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

        print("✅ База данных успешно инициализирована.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Ошибка установки: {e}")


if __name__ == "__main__":
    run_install()
