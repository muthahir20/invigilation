import streamlit as st
from db import login, get_duties
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

# PDF
def generate_pdf(name, dept, duties):
    file_path = f"{name}_{uuid.uuid4().hex}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("<b>INVIGILATION DUTY SCHEDULE</b>", styles['Title']))
    content.append(Spacer(1, 10))
    content.append(Paragraph(f"Name: {name}", styles['Normal']))
    content.append(Paragraph(f"Department: {dept}", styles['Normal']))
    content.append(Spacer(1, 10))

    data = [["S.No", "Session"]]
    for _, row in duties.iterrows():
        data.append([row["duty_order"], row["session_text"]])

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ]))

    content.append(table)
    doc.build(content)

    return file_path

# UI
st.markdown("<h2 style='text-align:center;'>👨‍🏫 Staff Login</h2>", unsafe_allow_html=True)

if st.session_state.user is None:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

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

        # ---------------- PDF ----------------
        file = generate_pdf(user["name"], user["dept"], duties)
        with open(file, "rb") as f:
            st.download_button("📄 Download PDF", f, file_name=file)

        st.markdown("### 📅 Your Duties")

        # ---------------- DUTY LIST ----------------
        for _, row in duties.iterrows():

            session = row["session_text"]

            # Detect FN / AN
            if "FN" in session.upper():
                card_class = "fn"
            elif "AN" in session.upper():
                card_class = "an"
            else:
                card_class = "other"

            st.markdown(f"""
            <div class="duty-card {card_class}">
                <b>Duty {row['duty_order']}</b><br>
                {session}
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("No duties assigned")