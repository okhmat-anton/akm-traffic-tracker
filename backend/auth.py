import streamlit as st
import hashlib
import psycopg2
import os
from streamlit_cookies_manager import EncryptedCookieManager
from db import get_user

# Инициализация Cookie Manager
cookies = EncryptedCookieManager(
    password=os.getenv("COOKIE_SECRET", "supersecretpassword"),
    prefix="tracker/"
)

if not cookies.ready():
    st.stop()

def hash_password(password):
    # st.write(hashlib.md5(('akm_' + password).encode()).hexdigest())
    return hashlib.md5(('akm_' + password).encode()).hexdigest()

# Установить куки
def set_cookie(name, value, days_expire=365):
    expiration = time.time() + days_expire * 24 * 60 * 60
    components.html(
        f"""
        <script>
        document.cookie = "{name}={value}; expires=" + new Date({int(expiration)} * 1000).toUTCString() + "; path=/";
        </script>
        """,
        height=0,
    )


# Автоматический логин через куки
def check_auto_login():
    username = cookies.get("username")
    password_hash = cookies.get("password_hash")

    if username:
        user = get_user(username)
        if user:
            db_username, db_password_hash = user
            if db_password_hash == password_hash:
                st.session_state.logged_in = True
                st.session_state.username = username
                if username == "tracker_admin":
                    st.session_state.role = "admin"
                else:
                    st.session_state.role = "user"
                st.rerun()
            else:
                logout()
        else:
            logout()


def login_page():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = get_user(username)
        if user:
            db_username, db_password_hash = user
            if db_password_hash == hash_password(password):
                st.success(f"Welcome, {db_username}!")
                st.session_state.logged_in = True
                st.session_state.username = db_username
                # cookies.set_cookie("username", db_username, max_age_days=365)
                # cookies.set_cookie("password_hash", hash_password(password), max_age_days=365)
                cookies["username"] = db_username
                cookies["password_hash"] = hash_password(password)
                cookies.save()
                if db_username == "tracker_admin":
                    st.session_state.role = "admin"
                else:
                    st.session_state.role = "user"
                st.rerun()
            else:
                st.error("Incorrect password")
        else:
            st.error("User not found")


def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

    cookies.delete("username")
    st.rerun()
