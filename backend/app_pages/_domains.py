import streamlit as st
import pandas as pd
from db import fetch_domains, add_domain, update_domain, delete_domain


def domains_page():
    st.subheader("Domains Management")

    if 'edit_domain_id' not in st.session_state:
        st.session_state.edit_domain_id = None

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

    st.subheader("Existing Domains")

    domains = fetch_domains()

    if not domains:
        st.info("No domains found.")
    else:
        # Стили для таблицы
        st.markdown(
            """
            <style>
            .styled-table {
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 12px;
                min-width: 400px;
                width: 100%;
            }
            .styled-table thead tr {
                background-color: #222225;
                color: #ffffff;
                text-align: left;
                font-weight: normal;
            }
            .styled-table th,
            .styled-table td {
                border: 1px solid rgb(46, 48, 58);
                padding: 4px 12px;
                font-weight: normal;
            }
            .styled-table tbody tr {
                border-bottom: 1px solid rgb(46, 48, 58);
            }
            .styled-table tbody tr:nth-of-type(even) {
                background-color: #14141b;
            }
            .styled-table tbody tr:hover {
                background-color: #1d1d21;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        df_data = {
            "Domain": [],
            "Redirect HTTPS": [],
            "Catch 404": [],
            "Default action": [],
            "Group": [],
            "Status": [],
            " ": [],  # Delete buttons
            "  ": [],  # Edit buttons
        }

        for i, domain in enumerate(domains):
            domain_id = domain.get('id')
            df_data["Domain"].append(domain.get("domain", ""))
            df_data["Redirect HTTPS"].append(domain.get("redirect_https", False))
            df_data["Catch 404"].append(domain.get("handle_404", False))
            df_data["Default action"].append(domain.get("default_company", ""))
            df_data["Group"].append(domain.get("group_name", ""))
            df_data["Status"].append(domain.get("status", ""))
            df_data[" "].append(f"<button href='?delete_id={domain_id}' class='st-button st-button-danger' id='del_{i}'>Delete</button>")
            df_data["  "].append(f"<button href='?edit_id={domain_id}' class='st-button st-button-primary' id='edit_{i}'>Edit</button>")

        # Создание DataFrame
        df = pd.DataFrame(df_data)

        # Отображение таблицы
        st.markdown(df.to_html(classes="styled-table", index=False, escape=False), unsafe_allow_html=True)


        ###################################
        ###################################

        st.markdown('<div class="table-container">', unsafe_allow_html=True)

        # Шапка таблицы
        st.markdown('<div class="table-header">', unsafe_allow_html=True)

        # Заголовок таблицы
        columns = st.columns((2, 1, 1, 2, 2, 1, 1, 1))  # Распределение ширины колонок
        columns[0].write("Domain")
        columns[1].write("Redirect HTTPS")
        columns[2].write("Catch 404")
        columns[3].write("Default Company")
        columns[4].write("Group")
        columns[5].write("Status")
        columns[6].write("Edit")
        columns[7].write("Delete")

        st.markdown('</div>', unsafe_allow_html=True)

        # Сами данные
        for domain in domains:
            domain_id = domain["id"]
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            cols = st.columns((2, 1, 1, 2, 2, 1, 1, 1))
            cols[0].write(domain["domain"])
            cols[1].write("✅" if domain["redirect_https"] else "❌")
            cols[2].write("✅" if domain["handle_404"] else "❌")
            cols[3].write(domain["default_company"])
            cols[4].write(domain["group_name"])
            cols[5].write(domain["status"])

            if cols[6].button('Edit', key=f"edit_{domain_id}"):
                st.session_state.edit_domain_id = domain_id
                st.rerun()

            if cols[7].button('Delete', key=f"delete_{domain_id}"):
                st.session_state.delete_domain_id = domain_id
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)




    # Редактирование записи
    if 'edit_domain_id' in st.session_state and st.session_state.edit_domain_id:
        edit_id = st.session_state.edit_domain_id
        domain_data = next((item for item in domains if item['id'] == edit_id), None)

        if domain_data:
            with st.form("edit_domain_form"):
                edit_domain = st.text_input("Domain", value=domain_data['domain'])
                edit_redirect_https = st.checkbox("Redirect to HTTPS", value=domain_data['redirect_https'])
                edit_handle_404 = st.selectbox("404 Handling", ["error", "redirect_to_company"],
                                               index=0 if domain_data['handle_404'] == 'error' else 1)
                edit_default_company = st.text_input("Default Company", value=domain_data['default_company'])
                edit_group_name = st.text_input("Group Name", value=domain_data['group_name'])
                edit_status = st.selectbox("Status", ["pending", "ok", "error"],
                                           index=["pending", "ok", "error"].index(domain_data['status']))
                submitted_edit = st.form_submit_button("Update Domain")

                if submitted_edit:
                    update_domain(
                        edit_id,
                        edit_domain,
                        edit_redirect_https,
                        edit_handle_404,
                        edit_default_company,
                        edit_group_name,
                        edit_status
                    )
                    st.session_state.edit_domain_id = None
                    st.success("Domain updated successfully!")
                    st.experimental_rerun()
