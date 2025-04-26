import streamlit as st
import psycopg2
import pandas as pd

DB_CONFIG = {
    'dbname': 'mydb',
    'user': 'myuser',
    'password': 'mypassword',
    'host': 'postgres'
}

def load_data():
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM clicks", conn)
    conn.close()
    return df

st.title("Клики пользователей")
data = load_data()
st.dataframe(data)
