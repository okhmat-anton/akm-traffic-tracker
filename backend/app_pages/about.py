import streamlit as st

def about_page():
    st.header("About Page")
    st.write("Welcome to the about page!")
    st.write(
        """
        This is a simple Streamlit application that demonstrates how to create a multi-page app.
        You can navigate between different pages using the sidebar.
        """
    )