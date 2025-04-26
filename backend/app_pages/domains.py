import streamlit as st
import pandas as pd
from db import fetch_domains, add_domain, update_domain, delete_domain
from streamlit_js_eval import streamlit_js_eval
import streamlit.components.v1 as components

from dataframe_with_button import static_dataframe
from dataframe_with_button import editable_dataframe


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
            "Id": [],
            "Domain": [],
            "Redirect HTTPS": [],
            "Catch 404": [],
            "Default action": [],
            "Group": [],
            "Status": [],
            # "": []
        }

        for i, domain in enumerate(domains):
            domain_id = domain.get('id')
            domain_link = domain.get("domain", "")
            df_data["Id"].append(domain_id)
            df_data["Domain"].append(domain_link)
            df_data["Redirect HTTPS"].append(domain.get("redirect_https", False))
            df_data["Catch 404"].append(domain.get("handle_404", False))
            df_data["Default action"].append(domain.get("default_company", ""))
            df_data["Group"].append(domain.get("group_name", ""))
            df_data["Status"].append(domain.get("status", ""))
            # df_data[""].append(f"""<a href='?mybutton=true'><button href='?delete_id={domain_id}' class='st-button st-button-danger' id='del_{i}'>Delete</button></a>&nbsp;&nbsp;&nbsp;<button href='?edit_id={domain_id}' class='st-button st-button-primary' id='edit_{i}'>Edit</button>""")

        # Создание DataFrame
        df = pd.DataFrame(df_data)
        result = static_dataframe(df, clickable_column="Id")
        st.dataframe(df)
        # Вывод результата клика
        if result:
            st.success(f"Ты нажал на строку с Id: {result}")
        # Отображение таблицы
        # st.markdown(result, unsafe_allow_html=True)



        if st.query_params.get("mybutton"):
            st.success("Нажал кнопку!")

        query_params = st.query_params
        if "delete_id" in query_params:
            st.warning(f"Удалить домен с id {query_params['delete_id']}")

        if "edit_id" in query_params:
            st.info(f"Редактировать домен с id {query_params['edit_id']}")

        ###############
        ###############
        ###############
        ###############
        ###############

        # # Пример доменов
        # domains = [
        #     {"id": 1, "domain": "google.com", "status": "Active"},
        #     {"id": 2, "domain": "facebook.com", "status": "Active"},
        #     {"id": 3, "domain": "twitter.com", "status": "Inactive"},
        # ]
        #
        # st.markdown("## Таблица доменов")
        #
        # # Заголовки таблицы
        # header_cols = st.columns([4, 2, 2, 2])  # ширина колонок
        # header_cols[0].markdown("**Домен**")
        # header_cols[1].markdown("**Статус**")
        # header_cols[2].markdown("**Редактировать**")
        # header_cols[3].markdown("**Удалить**")
        #
        # # Отрисовка строк
        # for domain in domains:
        #     domain_id = domain["id"]
        #     domain_link = domain["domain"]
        #     domain_status = domain["status"]
        #
        #     row_cols = st.columns([4, 2, 2, 2])
        #
        #     row_cols[0].write(domain_link)
        #     row_cols[1].write(domain_status)
        #
        #     with row_cols[2]:
        #         if st.button("Edit", key=f"edit_{domain_id}"):
        #             st.info(f"Редактируем {domain_link}")
        #
        #     with row_cols[3]:
        #         if st.button("Delete", key=f"delete_{domain_id}"):
        #             st.warning(f"Удаляем {domain_link}")

        df = pd.DataFrame({
            "BATCH_ID": ["item1", "item2", "item3"],
            "Name": ["Apple", "Banana", "Cherry"],
            "Price": [1.2, 0.8, 2.5],
            "IN_STOCK": [True, False, True],
            "EMAIL": ["abc@gmail.com", "cde@k.com", "abc@gmail.com"]
        })

        st.title("DataFrame with Buttons")

        # Генерируем HTML-кнопки через static_dataframe
        html_code = static_dataframe(df, clickable_column="BATCH_ID")

        # Выводим через markdown, разрешая HTML
        st.markdown(html_code, unsafe_allow_html=True)

        # Если клик был
        # if clicked:
        #     st.success(f"Clicked: {clicked}")
#######################
#######################
#######################
#######################
#######################

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
