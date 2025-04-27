import psycopg2
from psycopg2.extras import RealDictCursor


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://user:password@tracker_postgres/db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Функция подключения к базе
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(username):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def fetch_domains():
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM domains ORDER BY id DESC")
    domains = cur.fetchall()
    conn.close()
    return domains

def add_domain(domain, redirect_https, handle_404, default_company, group_name, status):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO domains (domain, redirect_https, handle_404, default_company, group_name, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (domain, redirect_https, handle_404, default_company, group_name, status))
    conn.commit()
    conn.close()

def update_domain(id, domain, redirect_https, handle_404, default_company, group_name, status):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE domains
        SET domain=%s, redirect_https=%s, handle_404=%s, default_company=%s, group_name=%s, status=%s, updated_at=NOW()
        WHERE id=%s
    """, (domain, redirect_https, handle_404, default_company, group_name, status, id))
    conn.commit()
    conn.close()

def delete_domain(id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM domains WHERE id = %s", (id,))
    conn.commit()
    conn.close()
