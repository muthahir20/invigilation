import streamlit as st
from db import login, get_duties, generate_staff_pdf
import uuid
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from ui import apply_ui
apply_ui()

# SESSION
if "user" not in st.session_state:
    st.session_state.user = None


# UI
st.markdown("<h2 style='text-align:center;'>Invigilation Duty Schedule - April 2026</h2>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Staff Login</h3>", unsafe_allow_html=True)

if st.session_state.user is None:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        email = st.text_input("Email (Official Mail ID)")
        password = st.text_input("Password (Bank Account Last 5 Digit)", type="password")

        if st.button("Login"):
            user = login(email.strip().lower(), password.strip())

            if user:
                st.session_state.user = {
                    "id": user[0],
                    "name": user[1],
                    "dept": user[2]
                }
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.markdown("For Login Issues Please Contact VP Academic - 9600016789", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    user = st.session_state.user

    st.success(f"Welcome {user['name']}")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    duties = get_duties(user["id"])

    if not duties.empty:

        # ---------------- DASHBOARD ----------------
        total_duties = len(duties)
        first_duty = duties.iloc[0]["session_text"]
        last_duty = duties.iloc[-1]["session_text"]

        st.markdown("### 📊 Your Duty Summary")

        col1, col2, col3 = st.columns(3)

        col1.markdown(
            f'<div class="stat-card fn">Total Duties<br>{total_duties}</div>',
            unsafe_allow_html=True
        )

        col2.markdown(
            f'<div class="stat-card an">First Duty<br>{first_duty}</div>',
            unsafe_allow_html=True
        )

        col3.markdown(
            f'<div class="stat-card other">Last Duty<br>{last_duty}</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        file = generate_staff_pdf(user["name"], user["dept"], duties)

        with open(file, "rb") as f:
            st.download_button(
                "📄 Download Duty Report",
                f,
                file_name=file
            )

        st.markdown("### 📅 Your Duties")

        # ---------------- DUTY LIST ----------------
        for i, (_, row) in enumerate(duties.iterrows(), start=1):

            session = row["session_text"]
            session_upper = session.upper()

            if "FN" in session_upper:
                card_class = "fn"
            elif "AN" in session_upper:
                card_class = "an"
            else:
                card_class = "other"

            st.markdown(f"""
            <div class="duty-card {card_class}">
                 <div style="display:flex; justify-content:space-between;">
                    <b>Duty {i}</b> 
                    {session}
                 </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("No duties assigned")

