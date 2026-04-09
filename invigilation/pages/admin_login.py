import streamlit as st
from db import admin_login, process_excel
from ui import apply_ui

apply_ui()

if "admin" not in st.session_state:
    st.session_state.admin = None

st.markdown('<div class="title">🛠️ Admin Panel</div>', unsafe_allow_html=True)

if not st.session_state.admin:

    st.markdown('<div class="card">', unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        admin = admin_login(username.strip(), password.strip())

        if admin:
            st.session_state.admin = {
                "id": admin[0],
                "role": admin[1]
            }
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown('</div>', unsafe_allow_html=True)

else:
    admin = st.session_state.admin

    st.success(f"Logged in as {admin['role']}")

    if st.button("Logout"):
        st.session_state.admin = None
        st.rerun()

    # ---------------- DASHBOARD ----------------
    st.markdown("### 📊 Admin Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.markdown('<div class="stat-card fn">👨‍🏫 Staff<br>250</div>', unsafe_allow_html=True)
    col2.markdown('<div class="stat-card an">📅 Exam Days<br>19</div>', unsafe_allow_html=True)
    col3.markdown('<div class="stat-card other">📝 Sessions<br>38</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- UPLOAD SECTION ----------------
    st.markdown("### 📤 Upload Data")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        if st.button("Upload Data"):
            try:
                process_excel(file)
                st.success("Uploaded successfully")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)