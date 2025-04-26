import streamlit as st
import pandas as pd
from db import fetch_domains, add_domain, update_domain, delete_domain

def domains_page():
    st.header("Domains Page")
    st.title("Domains Management")
    # Состояние для редактирования
    if 'edit_domain_id' not in st.session_state:
        st.session_state.edit_domain_id = None

    # Кнопка для добавления нового домена
    with st.expander("Add New Domain"):
        with st.form("add_domain_form"):
            new_domain = st.text_input("Domain (example.com)")
            new_redirect_https = st.checkbox("Redirect to HTTPS", value=True)
            new_handle_404 = st.selectbox("404 Handling", ["error", "redirect_to_company"])
            new_default_company = st.text_input("Default Company")
            new_group_name = st.text_input("Group Name")
            new_status = st.selectbox("Status", ["pending", "ok", "error"], index=0)
            submitted = st.form_submit_button("Add Domain")

            if submitted:
                if new_domain:
                    add_domain(
                        new_domain,
                        new_redirect_https,
                        new_handle_404,
                        new_default_company,
                        new_group_name,
                        new_status
                    )
                    st.success("Domain added successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Domain cannot be empty.")

    # Список доменов
    st.subheader("Existing Domains")

    try:
        domains = fetch_domains()
    except Exception as e:
        st.error(f"Error fetching domains: {e}")
        domains = []

    # Преобразуем в DataFrame для отображения
    if domains:
        df = pd.DataFrame(domains)

        # Отображаем только нужные поля
        df_display = df[[
            'domain', 'redirect_https', 'handle_404', 'default_company', 'group_name', 'status'
        ]]

        st.dataframe(df_display, use_container_width=True)

        # Теперь отдельно обработаем Edit и Delete
        for domain in domains:
            with st.container():
                cols = st.columns([5, 1, 1])
                cols[0].markdown(f"**{domain['domain']}** — {domain['status']}")
                if cols[1].button("Edit", key=f"edit_{domain['id']}"):
                    st.session_state.edit_domain_id = domain['id']
                if cols[2].button("Delete", key=f"delete_{domain['id']}"):
                    delete_domain(domain['id'])
                    st.success("Domain deleted successfully!")
                    st.experimental_rerun()

                if st.session_state.edit_domain_id == domain['id']:
                    with st.form(f"edit_domain_form_{domain['id']}"):
                        edit_domain = st.text_input("Domain", value=domain['domain'])
                        edit_redirect_https = st.checkbox("Redirect to HTTPS", value=domain['redirect_https'])
                        edit_handle_404 = st.selectbox("404 Handling", ["error", "redirect_to_company"],
                                                       index=0 if domain['handle_404'] == 'error' else 1)
                        edit_default_company = st.text_input("Default Company", value=domain['default_company'] or "")
                        edit_group_name = st.text_input("Group Name", value=domain['group_name'] or "")
                        edit_status = st.selectbox("Status", ["pending", "ok", "error"],
                                                   index=["pending", "ok", "error"].index(domain['status']))
                        save_changes = st.form_submit_button("Save Changes")

                        if save_changes:
                            update_domain(
                                domain['id'],
                                edit_domain,
                                edit_redirect_https,
                                edit_handle_404,
                                edit_default_company,
                                edit_group_name,
                                edit_status
                            )
                            st.success("Domain updated successfully!")
                            st.session_state.edit_domain_id = None
                            st.experimental_rerun()
    else:
        st.info("No domains found. Add a new one above.")