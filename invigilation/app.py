import streamlit as st
from ui import apply_ui

st.set_page_config(page_title="Invigilation System", layout="wide")

apply_ui()

# Sidebar Navigation
# st.sidebar.title("📊 Navigation")
# page = st.sidebar.radio("Go to", ["Home", "Staff", "Admin"])

# Header
st.markdown('<div class="title">THE NEW COLLEGE</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Invigilation Management System</div>', unsafe_allow_html=True)

st.info("👈 Use sidebar to navigate\n\n👨‍🏫 Staff Login\n🛠️ Admin Panel")

# if page == "Home":
    

# elif page == "Staff":
#     st.switch_page("pages/staff_login.py")

# elif page == "Admin":
#     st.switch_page("pages/admin_login.py")
