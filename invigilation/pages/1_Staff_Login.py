import streamlit as st
from db import staff_login, get_duties

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="Staff Login", layout="centered")

# -----------------------------------
# SESSION STATE
# -----------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------------
# HELPER FUNCTION
# -----------------------------------
def get_session_class(session):
    session = str(session).lower()
    if "fn" in session:
        return "fn"
    elif "an" in session:
        return "an"
    return "other"

# -----------------------------------
# PDF FUNCTION
# -----------------------------------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
# -----------------------------------
# WATERMARK FUNCTION
# -----------------------------------
def add_watermark(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 60)
    canvas_obj.setFillColorRGB(0.9, 0.9, 0.9)

    canvas_obj.drawCentredString(
        A4[0] / 2,
        A4[1] / 2,
        "CONFIDENTIAL"
    )

    canvas_obj.restoreState()

# -----------------------------------
# MAIN PDF
# -----------------------------------
def generate_pdf(name, dept, duties):

    file_path = f"{name}_duty.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    content = []

    # -----------------------------------
    # HEADER WITH LOGO
    # -----------------------------------
  

    logo_path = "logo.png"

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=60, height=60)
        header = [[logo, Paragraph("<b>THE NEW COLLEGE</b>", styles['Title'])]]
    else:
     header = [["", Paragraph("<b>THE NEW COLLEGE</b>", styles['Title'])]]

    header_table = Table(header, colWidths=[70, 400])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))

    content.append(header_table)
    content.append(Spacer(1, 5))

    content.append(Paragraph("<centre>An Autonmous Instutution Affiliated to Madras University</centre>", styles['Normal']))
    content.append(Spacer(1, 10))

    # Divider
    content.append(Table([[""]], colWidths=[500], rowHeights=[1],
        style=[("BACKGROUND", (0,0), (-1,-1), colors.black)]))
    content.append(Spacer(1, 10))

    # -----------------------------------
    # TITLE
    # -----------------------------------
    content.append(Paragraph("<b>INVIGILATION DUTY SCHEDULE</b>", styles['Title']))
    content.append(Spacer(1, 15))

    # -----------------------------------
    # STAFF DETAILS
    # -----------------------------------
    info_table = Table([
        ["Name", name],
        ["Department", dept],
        ["Total Duties", str(len(duties))]
    ], colWidths=[150, 300])

    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("PADDING", (0,0), (-1,-1), 8),
    ]))

    content.append(info_table)
    content.append(Spacer(1, 20))

    # -----------------------------------
    # DUTY TABLE
    # -----------------------------------
    data = [["S.No", "Session Details"]]

    for _, row in duties.iterrows():
        data.append([str(row["duty_order"]), row["session_text"]])

    duty_table = Table(data, colWidths=[60, 390])

    style = [
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]

    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0,i), (-1,i), colors.whitesmoke))

    duty_table.setStyle(TableStyle(style))

    content.append(duty_table)
    content.append(Spacer(1, 25))

    # -----------------------------------
    # INSTRUCTIONS
    # -----------------------------------
    content.append(Paragraph("<b>Instructions</b>", styles['Heading3']))
    content.append(Spacer(1, 8))

    instructions = [
        "• Report 15 minutes before the session.",
        "• Verify student identity.",
        "• Maintain discipline.",
        "• Follow exam rules strictly."
    ]

    for ins in instructions:
        content.append(Paragraph(ins, styles['Normal']))
        content.append(Spacer(1, 4))

    content.append(Spacer(1, 35))

    # -----------------------------------
    # SIGNATURES
    # -----------------------------------
    sign_table = Table([
        ["________________________", "________________________"],
        ["Controller of Examinations", "Principal"]
    ], colWidths=[250, 250])

    sign_table.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    content.append(sign_table)

    # BUILD WITH WATERMARK
    doc.build(content, onFirstPage=add_watermark, onLaterPages=add_watermark)

    return file_path

    # -----------------------------------
    # DUTY TABLE
    # -----------------------------------
    data = [["S.No", "Session Details"]]

    for _, row in duties.iterrows():
        data.append([str(row["duty_order"]), row["session_text"]])

    duty_table = Table(data, colWidths=[60, 390])

    # Zebra rows
    style = [
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]

    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0,i), (-1,i), colors.whitesmoke))

    duty_table.setStyle(TableStyle(style))

    content.append(duty_table)
    content.append(Spacer(1, 25))

    # -----------------------------------
    # INSTRUCTIONS
    # -----------------------------------
    content.append(Paragraph("<b>Instructions</b>", styles['Heading3']))
    content.append(Spacer(1, 8))

    instructions = [
        "• Report to the exam hall at least 15 minutes before the session.",
        "• Ensure proper verification of student identity.",
        "• Do not allow malpractice under any circumstances.",
        "• Follow all examination rules strictly.",
        "• Submit reports immediately after duty."
    ]

    for ins in instructions:
        content.append(Paragraph(ins, styles['Normal']))
        content.append(Spacer(1, 4))

    content.append(Spacer(1, 35))

    # -----------------------------------
    # SIGNATURE SECTION
    # -----------------------------------
    sign_table = Table([
        ["________________________", "________________________"],
        ["Controller of Examinations", "Principal"]
    ], colWidths=[250, 250])

    sign_table.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 10),
    ]))

    content.append(sign_table)

    # BUILD
    doc.build(content)

    return file_path

# -----------------------------------
# MODERN CSS
# -----------------------------------
st.markdown("""
<style>

/* Card */
.card {
    width: 100%;
    max-width: 500px;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    margin: 20px auto;
}

/* Light Mode */
@media (prefers-color-scheme: light) {
    .card { background: #1e1e1e; color: white; }
    .duty-card { background:#2b2b2b; color:white; }
    .stat-card { background:#2b2b2b; color:white; }
}

/* Dark Mode */
@media (prefers-color-scheme: dark) {
    .card { background: #ffffff; color: black; }
    .duty-card { background:#f5f5f5; color:black; }
    .stat-card { background:#f5f5f5; color:black; }
}

/* Duty Card */
.duty-card {
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}

/* Stats */
.stat-card {
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    font-weight: bold;
}

/* Session Colors */
.fn { border-left: 5px solid #4CAF50; }
.an { border-left: 5px solid #2196F3; }
.other { border-left: 5px solid #9C27B0; }

/* Title */
.title {
    text-align:center;
    font-size:32px;
    font-weight:700;
    margin-bottom:10px;
}

/* Buttons */
.stButton > button {
    width: 100%;
    border-radius: 10px;
}
.card:empty {
    display: none;
    }

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# TITLE
# -----------------------------------
st.markdown('<div class="title">👨‍🏫 Staff Login</div>', unsafe_allow_html=True)

# -----------------------------------
# LOGIN
# -----------------------------------
if st.session_state.user is None:

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Login")

    email = st.text_input("Email", key="staff_email")
    password = st.text_input("Password", type="password", key="staff_pass")

    if st.button("Login", key="staff_login"):
        user = staff_login(email, password)

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

# -----------------------------------
# DASHBOARD
# -----------------------------------
else:
    user = st.session_state.user
    duties = get_duties(user["id"])

    # PROFILE CARD
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(f"""
    <h3>👋 Welcome, {user['name']}</h3>
    <p><b>Department:</b> {user['dept']}</p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚪 Logout", key="logout"):
            st.session_state.user = None
            st.rerun()

    with col2:
        if not duties.empty:
            if st.button("📄 Generate PDF", key="pdf"):
                file = generate_pdf(user["name"], user["dept"], duties)
                with open(file, "rb") as f:
                    st.download_button("⬇️ Download", f, file_name=file)

    st.markdown('</div>', unsafe_allow_html=True)

    # STATS
    if not duties.empty:

        total = len(duties)
        first = duties.iloc[0]["session_text"]
        last = duties.iloc[-1]["session_text"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f'<div class="stat-card">📊 Total<br>{total}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown(f'<div class="stat-card">🌅 First<br>{first}</div>', unsafe_allow_html=True)

        with col3:
            st.markdown(f'<div class="stat-card">🌙 Last<br>{last}</div>', unsafe_allow_html=True)

    # DUTIES
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📅 Your Duties")

    if not duties.empty:
        for _, row in duties.iterrows():
            cls = get_session_class(row["session_text"])

            st.markdown(f"""
            <div class="duty-card {cls}">
                <b>Duty {row['duty_order']}</b><br>
                {row['session_text']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No duties assigned")

    st.markdown('</div>', unsafe_allow_html=True)