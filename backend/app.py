import streamlit as st

st.set_page_config(page_title="Tracker Panel", page_icon="⚙️", layout="wide")

from auth import login_page
from app_pages.about import about_page
from app_pages.affiliates import affiliates_page
from app_pages.dashboard import dashboard_page
from app_pages.domains import domains_page
from app_pages.landings import landings_page
from app_pages.offers import offers_page
from app_pages.reports import reports_page
from app_pages.settings import settings_page
from app_pages.campaigns import campaigns_page
from app_pages.sources import sources_page
from app_pages.users import users_page
from auth import check_auto_login, logout

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True

st.session_state.logged_in = check_auto_login()

if st.session_state.logged_in:

    st.markdown(f"<h4>Welcome, {st.session_state.username} ({st.session_state.role})</h4>", unsafe_allow_html=True)

    if st.button("Logout", key="logout"):
        logout()

    tabs = st.tabs(["Dashboard",
                    "Campaigns",
                    "Landing Pages",
                    "Affiliate Networks",
                    "Offers",
                    "Sources",
                    "Reports",
                    "Domains",
                    "Settings",
                    "Users",
                    "About",
                ])

    with tabs[0]:
        dashboard_page()
    with tabs[1]:
        campaigns_page()
    with tabs[2]:
        landings_page()
    with tabs[3]:
        affiliates_page()
    with tabs[4]:
        offers_page()
    with tabs[5]:
        sources_page()
    with tabs[6]:
        reports_page()
    with tabs[7]:
        domains_page()
    with tabs[8]:
        settings_page()
    with tabs[9]:
        users_page()
    with tabs[10]:
        about_page()

else:
    login_page()
