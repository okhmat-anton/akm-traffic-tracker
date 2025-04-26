import streamlit as st
import hashlib
import streamlit.components.v1 as components
import time
from db import get_user

def hash_password(password):
    # st.write(hashlib.md5(('akm_' + password).encode()).hexdigest())
    return hashlib.md5(('akm_' + password).encode()).hexdigest()

def set_cookie(name, value, days_expire=7):
    expiration = time.time() + days_expire * 24 * 60 * 60
    components.html(
        f"""
        <script>
        document.cookie = "{name}={value}; expires=" + new Date({int(expiration)} * 1000).toUTCString() + "; path=/";
        </script>
        """,
        height=0,
    )

def get_cookie(name):
    cookie_value = st.query_params.get(name)
    return cookie_value[0] if cookie_value else None

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
                set_cookie("username", username)
                set_cookie("password_hash", db_password_hash)
            else:
                st.error("Incorrect password")
        else:
            st.error("User not found")
