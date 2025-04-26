import psycopg2

def connect_db():
    return psycopg2.connect(
        host="tracker_postgres",
        database="db",
        user="user",
        password="password"
    )

def get_user(username):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user
