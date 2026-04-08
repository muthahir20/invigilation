import streamlit as st
from ui import apply_ui

st.set_page_config(page_title="Invigilation System")

apply_ui()

st.markdown('<div class="title">THE NEW COLLEGE</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">INVIGILATION SCHEDULE</div>', unsafe_allow_html=True)

st.info("👈 Use sidebar to navigate\n\n👨‍🏫 Staff\n🛠️ Admin")