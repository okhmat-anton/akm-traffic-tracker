import streamlit as st
from auth import login_page, get_cookie, get_user

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Автологин через куки
cookie_username = get_cookie("username")
cookie_password_hash = get_cookie("password_hash")
if cookie_username and cookie_password_hash:
    user = get_user(cookie_username)
    if user:
        db_username, db_password_hash = user
        if db_password_hash == cookie_password_hash:
            st.session_state.logged_in = True
            st.session_state.username = db_username

# Вывод интерфейса
if st.session_state.logged_in:
    st.write(f"You are logged in as {st.session_state.username}")
else:
    login_page()
