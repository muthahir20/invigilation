import streamlit as st
from db import admin_login, process_excel
from ui import apply_ui

apply_ui()

if "admin" not in st.session_state:
    st.session_state.admin = False

if "role" not in st.session_state:
    st.session_state.role = None

st.markdown('<div class="title">🛠️ Admin Panel</div>', unsafe_allow_html=True)

if not st.session_state.admin:

    st.markdown('<div class="card">', unsafe_allow_html=True)

    username = st.text_input("Username", key="admin_user")
    password = st.text_input("Password", type="password", key="admin_pass")

    if st.button("Login", key="admin_login"):
        admin = admin_login(username, password)
        if admin:
            st.session_state.admin = True
            st.session_state.role = admin[1]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.success(f"Logged in as {st.session_state.role}")

    if st.button("Logout", key="admin_logout"):
        st.session_state.admin = False
        st.session_state.role = None
        st.rerun()

    st.markdown('<div class="card">', unsafe_allow_html=True)

    file = st.file_uploader("Upload Excel", type=["xlsx"], key="upload")

    if file:
        if st.button("Upload Data", key="upload_btn"):
            process_excel(file)
            st.success("Uploaded successfully")

    st.markdown('</div>', unsafe_allow_html=True)