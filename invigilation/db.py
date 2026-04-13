from sqlalchemy import create_engine, text
import pandas as pd
import hashlib
import streamlit as st

# -----------------------------------
# DB CONNECTION
# -----------------------------------
USERNAME = st.secrets["DB_USERNAME"]
PASSWORD = st.secrets["DB_PASSWORD"]
HOST = st.secrets["DB_HOST"]
PORT = st.secrets["DB_PORT"]
DATABASE = st.secrets["DB_NAME"]

engine = create_engine(
    f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}",
    connect_args={
        "ssl": {
            "ca": "",
            "check_hostname": False
        }
    },
    pool_pre_ping=True,
    pool_recycle=1800
)
import io

def process_excel(file):
    xls = pd.ExcelFile(io.BytesIO(file))

# -----------------------------------
# HASH
# -----------------------------------
def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

# -----------------------------------
# STAFF LOGIN
# -----------------------------------
def login(email, password):
    hashed = hash_password(password)

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT staff_id, name, dept 
                FROM staff 
                WHERE TRIM(LOWER(email)) = TRIM(LOWER(:email))
                AND bank_last5 = :password
            """),
            {"email": email, "password": hashed}
        ).fetchone()

    return result

# -----------------------------------
# ADMIN LOGIN
# -----------------------------------
def admin_login(username, password):
    hashed = hash_password(password)

    with engine.connect() as conn:
        return conn.execute(
            text("""
                SELECT id, role FROM admin_users
                WHERE username = :username AND password = :password
            """),
            {"username": username, "password": hashed}
        ).fetchone()

# -----------------------------------
# GET DUTIES
# -----------------------------------
def get_duties(staff_id):
    query = text("""
        SELECT session_text, duty_order
        FROM duty
        WHERE staff_id = :staff_id
        ORDER BY duty_order
    """)

    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"staff_id": staff_id})

# -----------------------------------
# PROCESS EXCEL (SAFE VERSION)
# -----------------------------------
import io
from sqlalchemy import text
import pandas as pd


def process_excel(file, mode="replace"):

    # ---------------- READ FILE ----------------
    xls = pd.ExcelFile(io.BytesIO(file))

    staff_sheet = None
    duty_sheet = None

    for sheet in xls.sheet_names:
        name = sheet.strip().lower()

        if "staff" in name:
            staff_sheet = sheet
        elif "duty" in name:
            duty_sheet = sheet

    if not staff_sheet:
        raise Exception(f"❌ Staff sheet not found. Available sheets: {xls.sheet_names}")

    if not duty_sheet:
        raise Exception(f"❌ Duty sheet not found. Available sheets: {xls.sheet_names}")

    # ---------------- LOAD DATA ----------------
    staff_df = pd.read_excel(xls, sheet_name=staff_sheet)
    duty_df = pd.read_excel(xls, sheet_name=duty_sheet)

    # ---------------- CLEAN COLUMN NAMES ----------------
    staff_df.columns = staff_df.columns.str.strip().str.lower()
    duty_df.columns = duty_df.columns.str.strip().str.lower()

    # ---------------- VALIDATE REQUIRED COLUMNS ----------------
    required_staff = {"id", "name", "dept", "email", "bank_last5"}
    required_duty = {"id", "session", "order"}

    if not required_staff.issubset(staff_df.columns):
        raise Exception(f"❌ Staff sheet missing columns: {required_staff}")

    if not required_duty.issubset(duty_df.columns):
        raise Exception(f"❌ Duty sheet missing columns: {required_duty}")

    # ---------------- RENAME ----------------
    staff_df = staff_df.rename(columns={
        "id": "staff_id",
        "session": "session_text"
    })

    duty_df = duty_df.rename(columns={
        "id": "staff_id",
        "session": "session_text",
        "order": "duty_order"
    })

    # ---------------- EMPTY CHECK ----------------
    if staff_df.empty:
        raise Exception("❌ Staff sheet is empty")

    if duty_df.empty:
        raise Exception("❌ Duty sheet is empty")

    # ---------------- CLEAN DATA ----------------
    staff_df["staff_id"] = staff_df["staff_id"].astype(str).str.strip()
    duty_df["staff_id"] = duty_df["staff_id"].astype(str).str.strip()

    staff_df["email"] = staff_df["email"].astype(str).str.strip().str.lower()
    staff_df["bank_last5"] = staff_df["bank_last5"].astype(str).str.strip()

    duty_df["session_text"] = duty_df["session_text"].astype(str).str.strip()

    # ---------------- HASH PASSWORD ----------------
    staff_df["bank_last5"] = staff_df["bank_last5"].apply(hash_password)

    # ---------------- KEEP REQUIRED ----------------
    staff_df = staff_df[["staff_id", "name", "dept", "email", "bank_last5"]]
    duty_df = duty_df[["staff_id", "session_text", "duty_order"]]

    # ---------------- DB OPERATION ----------------
    with engine.begin() as conn:

        if mode == "replace":
            # 🔥 FULL RESET
            conn.execute(text("DELETE FROM duty"))
            conn.execute(text("DELETE FROM staff"))

        elif mode == "append":

            # 🚫 REMOVE EXISTING STAFF
            existing_staff = pd.read_sql("SELECT staff_id FROM staff", conn)
            staff_df = staff_df[~staff_df["staff_id"].isin(existing_staff["staff_id"])]

            # 🚫 REMOVE DUPLICATE DUTIES
            existing_duty = pd.read_sql("SELECT staff_id, session_text FROM duty", conn)

            duty_df = duty_df.merge(
                existing_duty,
                on=["staff_id", "session_text"],
                how="left",
                indicator=True
            )

            duty_df = duty_df[duty_df["_merge"] == "left_only"]
            duty_df = duty_df.drop(columns=["_merge"])

        # ---------------- INSERT ----------------
        if not staff_df.empty:
            staff_df.to_sql("staff", conn, if_exists="append", index=False)

        if not duty_df.empty:
            duty_df.to_sql("duty", conn, if_exists="append", index=False)

    print("✅ Data inserted successfully")

def get_filtered_duties(session=None, dept=None, staff_ids=None):

    query = """
        SELECT s.staff_id, s.name, s.dept, d.session_text
        FROM staff s
        JOIN duty d ON s.staff_id = d.staff_id
        WHERE 1=1
    """

    params = {}

    if session and session != "All":
        query += " AND d.session_text = :session"
        params["session"] = session

    if dept and dept != "All":
        query += " AND s.dept = :dept"
        params["dept"] = dept

    if staff_ids and "All" not in staff_ids:
        placeholders = ",".join([f":id{i}" for i in range(len(staff_ids))])
        query += f" AND s.staff_id IN ({placeholders})"

        for i, val in enumerate(staff_ids):
            params[f"id{i}"] = val

    query += " ORDER BY d.session_text, s.staff_id"

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    return df

def get_dashboard_stats():
    with engine.connect() as conn:
        staff = conn.execute(text("SELECT COUNT(*) FROM staff")).scalar()
        duty = conn.execute(text("SELECT COUNT(*) FROM duty")).scalar()
        sessions = conn.execute(text("SELECT COUNT(DISTINCT session_text) FROM duty")).scalar()

    return staff, duty, sessions


def get_fn_an_count():
    with engine.connect() as conn:
        fn = conn.execute(text("SELECT COUNT(*) FROM duty WHERE session_text LIKE '%FN%'")).scalar()
        an = conn.execute(text("SELECT COUNT(*) FROM duty WHERE session_text LIKE '%AN%'")).scalar()

    return fn, an

def update_admin_password(admin_id, old_password, new_password):
    old_hashed = hash_password(old_password)
    new_hashed = hash_password(new_password)

    with engine.begin() as conn:
        # Check old password
        result = conn.execute(
            text("""
                SELECT id FROM admin_users
                WHERE id = :id AND password = :old_password
            """),
            {"id": admin_id, "old_password": old_hashed}
        ).fetchone()

        if not result:
            return False  # old password incorrect

        # Update password
        conn.execute(
            text("""
                UPDATE admin_users
                SET password = :new_password
                WHERE id = :id
            """),
            {"id": admin_id, "new_password": new_hashed}
        )

    return True

def transfer_duty_session(session, from_staff, to_staff):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE duty
                SET staff_id = :to_staff
                WHERE staff_id = :from_staff
                AND session_text = :session
            """),
            {
                "from_staff": from_staff,
                "to_staff": to_staff,
                "session": session
            }
        )

def swap_duties_session(session, staff1, staff2):
    with engine.begin() as conn:

        # temp swap
        conn.execute(text("""
            UPDATE duty SET staff_id = 'TEMP_SWAP'
            WHERE staff_id = :s1 AND session_text = :session
        """), {"s1": staff1, "session": session})

        conn.execute(text("""
            UPDATE duty SET staff_id = :s1
            WHERE staff_id = :s2 AND session_text = :session
        """), {"s1": staff1, "s2": staff2, "session": session})

        conn.execute(text("""
            UPDATE duty SET staff_id = :s2
            WHERE staff_id = 'TEMP_SWAP'
            AND session_text = :session
        """), {"s2": staff2})


def delete_duty_session(staff_id, session):
    with engine.begin() as conn:
        conn.execute(
            text("""
                DELETE FROM duty
                WHERE staff_id = :staff_id
                AND session_text = :session
            """),
            {"staff_id": staff_id, "session": session}
        )

def add_new_duty(staff_id, session):
    with engine.begin() as conn:

        # prevent duplicate
        existing = conn.execute(
            text("""
                SELECT 1 FROM duty
                WHERE staff_id = :staff_id
                AND session_text = :session
            """),
            {"staff_id": staff_id, "session": session}
        ).fetchone()

        if existing:
            return False

        # get next order
        max_order = conn.execute(
            text("SELECT COALESCE(MAX(duty_order),0) FROM duty WHERE staff_id = :staff_id"),
            {"staff_id": staff_id}
        ).scalar()

        conn.execute(
            text("""
                INSERT INTO duty (staff_id, session_text, duty_order)
                VALUES (:staff_id, :session, :order)
            """),
            {
                "staff_id": staff_id,
                "session": session,
                "order": max_order + 1
            }
        )

    return True

def transfer_multiple_duties(sessions, from_staff, to_staff):

    if not sessions:
        return

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE duty
                SET staff_id = :to_staff
                WHERE staff_id = :from_staff
                AND session_text IN :sessions
            """),
            {
                "from_staff": from_staff,
                "to_staff": to_staff,
                "sessions": tuple(sessions)
            }
        )

def delete_multiple_duties(staff_id, sessions):

    if not sessions:
        return

    with engine.begin() as conn:
        for session in sessions:
            conn.execute(
                text("""
                    DELETE FROM duty
                    WHERE staff_id = :staff_id
                    AND session_text = :session
                """),
                {
                    "staff_id": staff_id,
                    "session": session
                }
            )

def add_multiple_duties(staff_id, sessions):

    if not sessions:
        return False

    with engine.begin() as conn:

        existing = pd.read_sql(
            text("""
                SELECT session_text FROM duty
                WHERE staff_id = :staff_id
            """),
            conn,
            params={"staff_id": staff_id}
        )["session_text"].tolist()

        new_rows = []

        for session in sessions:
            if session not in existing:
                new_rows.append({
                    "staff_id": staff_id,
                    "session_text": session,
                    "duty_order": 0
                })

        if new_rows:
            pd.DataFrame(new_rows).to_sql(
                "duty",
                conn,
                if_exists="append",
                index=False
            )

    # 🔥 IMPORTANT
    reorder_duties(staff_id)

    return True

import re

def reorder_duties(staff_id):

    with engine.begin() as conn:

        df = pd.read_sql(
            text("""
                SELECT session_text
                FROM duty
                WHERE staff_id = :staff_id
            """),
            conn,
            params={"staff_id": staff_id}
        )

        if df.empty:
            return

        # ---------------- SORT LOGIC ----------------
        def sort_key(session):

            # Extract day number
            day_match = re.search(r'\d+', session)
            day = int(day_match.group()) if day_match else 0

            # FN before AN
            if "FN" in session.upper():
                slot = 0
            elif "AN" in session.upper():
                slot = 1
            else:
                slot = 2

            return (day, slot)

        df = df.sort_values(by="session_text", key=lambda col: col.map(sort_key))

        # ---------------- UPDATE ORDER ----------------
        for i, row in enumerate(df.itertuples(), start=1):
            conn.execute(
                text("""
                    UPDATE duty
                    SET duty_order = :order
                    WHERE staff_id = :staff_id
                    AND session_text = :session
                """),
                {
                    "order": i,
                    "staff_id": staff_id,
                    "session": row.session_text
                }
            )

def get_session_report(session_text):

    query = text("""
        SELECT d.session_text, s.staff_id, s.name, s.dept
        FROM duty d
        JOIN staff s ON d.staff_id = s.staff_id
        WHERE d.session_text = :session
        ORDER BY s.staff_id
    """)

    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"session": session_text})


def get_staff_report(staff_id):

    query = text("""
        SELECT d.session_text, d.duty_order
        FROM duty d
        WHERE d.staff_id = :staff_id
        ORDER BY d.duty_order
    """)

    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"staff_id": staff_id})

import re
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet

def generate_session_pdf(session, df):

    # ---------------- SAFE FILE NAME ----------------
    safe_session = re.sub(r'[^\w\- ]', '_', session)

    folder = "reports"
    os.makedirs(folder, exist_ok=True)

    file = os.path.join(folder, f"session_{safe_session}.pdf")

    doc = SimpleDocTemplate(file, pagesize=A4)

    # ---------------- STYLES (DEFAULT FONT) ----------------
    title_style = ParagraphStyle(
        name="Title",
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=18,
        spaceAfter=6
    )

    center_style = ParagraphStyle(
        name="Center",
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=8
    )

    normal_style = ParagraphStyle(
        name="Normal",
        alignment=TA_LEFT,
        fontName="Helvetica",
        fontSize=11
    )

    title_style = ParagraphStyle(
        name="Normal",
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=11
    )

    # 🔥 WRAP STYLE (IMPORTANT)
    styles = getSampleStyleSheet()
    wrap_style = styles["Normal"]

    content = []

    # ---------------- HEADER ----------------
    content.append(Paragraph("<b>THE NEW COLLEGE</b>", title_style))
    content.append(Spacer(1, 10))

    content.append(Paragraph(
        "(AN AUTONOMOUS INSTITUTION AFFILIATED TO THE UNIVERSITY OF MADRAS<br/>"
        "& ACCREDITED BY NAAC WITH 'A++' GRADE IN THE 4th CYCLE)<br/>"
        "Old No.87 / New No.147, Peters Road, Royapettah, Chennai - 600 014.",
        center_style
    ))

    content.append(Spacer(1, 10))

    # ---------------- EXAM TITLE ----------------
    content.append(Paragraph(
        "<b>AUTONOMOUS EXAMINATIONS – APRIL 2026</b>",
        title_style
    ))

    content.append(Spacer(1, 10))

    # ---------------- REPORT TITLE ----------------
    content.append(Paragraph("<b>SESSION DUTY REPORT</b>", title_style))

    content.append(Spacer(1, 10))

    # ---------------- SESSION INFO ----------------
    content.append(Paragraph(f"<b>Session:</b> {session}", normal_style))
    content.append(Paragraph(f"<b>Total Staff:</b> {len(df)}", normal_style))

    content.append(Spacer(1, 10))

    # ---------------- TABLE ----------------
    data = [["S.No", "Name", "Department"]]

    for i, (_, row) in enumerate(df.iterrows(), start=1):

        name = Paragraph(str(row.get("name", "")), wrap_style)
        dept = Paragraph(str(row.get("dept", "-")), wrap_style)

        data.append([
            i,
            name,
            dept
        ])

    table = Table(data, colWidths=[50, 230, 200], repeatRows=1)

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

        # Alignments
        ("ALIGN", (0,0), (0,-1), "CENTER"),
        ("ALIGN", (1,1), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

        # 🔥 PADDING (improves readability)
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    content.append(table)

    # ---------------- BUILD ----------------
    doc.build(content)

    return file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import re


from reportlab.platypus import Image
import os

def generate_staff_pdf(staff_name, dept, df):

    # ---------------- SAFE FILE NAME ----------------
    safe_name = staff_name.replace(" ", "_")
    file = f"{safe_name}_report.pdf"

    doc = SimpleDocTemplate(file, pagesize=A4)
    styles = getSampleStyleSheet()

    # ---------------- CUSTOM STYLES ----------------
    title_style = ParagraphStyle(name="Title", alignment=TA_CENTER, fontSize=18)
    center_style = ParagraphStyle(name="Center", alignment=TA_CENTER, fontSize=9)
    normal_style = ParagraphStyle(name="Normal", alignment=TA_LEFT, fontSize=11)

    content = []

    # ---------------- HEADER ----------------
    content.append(Paragraph("<b>THE NEW COLLEGE</b> <br/>", title_style))
    content.append(Spacer(1, 12))
    
    content.append(Paragraph(
        "(AN AUTONOMOUS INSTITUTION AFFILIATED TO THE UNIVERSITY OF MADRAS<br/>"
        "& ACCREDITED BY NAAC WITH 'A++' GRADE IN THE 4th CYCLE)<br/>"
        "Old No.87 / New No.147, Peters Road, Royapettah, Chennai - 600 014.",
        center_style
    ))

    content.append(Spacer(1, 12))

    # ---------------- EXAM TITLE ----------------
    content.append(Paragraph(
        "<b>SEMESTER EXAMINATIONS – APRIL 2026</b>",
        center_style
    ))

    content.append(Spacer(1, 12))

    content.append(Paragraph(
        "<b>INVIGILATION DUTY ORDER</b>",
        center_style
    ))

    content.append(Spacer(1, 12))

    # ---------------- BODY ----------------
    content.append(Paragraph(f"<b>Name:</b> {staff_name}", styles['Normal']))
    content.append(Paragraph(f"<b>Department:</b> {dept}", styles['Normal']))
    content.append(Spacer(1, 10))

    # ---------------- SUMMARY ----------------
    total_duties = len(df)

    first_duty = df.iloc[0]["session_text"] if total_duties > 0 else "-"
    last_duty = df.iloc[-1]["session_text"] if total_duties > 0 else "-"

    content.append(Paragraph(f"<b>Total Duties:</b> {total_duties}", styles['Normal']))
    content.append(Paragraph(f"<b>First Duty:</b> {first_duty}", styles['Normal']))
    content.append(Paragraph(f"<b>Last Duty:</b> {last_duty}", styles['Normal']))
    content.append(Spacer(1, 12))

    # ---------------- TITLE ----------------
    content.append(Paragraph("<b>DATE & SESSION</b>", center_style))
    content.append(Spacer(1, 8))

    # ---------------- TABLE ----------------
    data = [["S.No", "Date", "Day", "Session"]]

    for i, row in enumerate(df.itertuples(), start=1):

        session = row.session_text

        date_match = re.search(r"\d{2}/\d{2}/\d{4}", session)

        if date_match:
            date_str = date_match.group()
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                day_name = date_obj.strftime("%A")
            except:
                day_name = "-"
        else:
            date_str = "-"
            day_name = "-"

        if "FN" in session.upper():
            session_type = "FN"
        elif "AN" in session.upper():
            session_type = "AN"
        else:
            session_type = session

        data.append([i, date_str, day_name, session_type])

    table = Table(data, colWidths=[60, 130, 130, 130], repeatRows=1)

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    content.append(table)

    content.append(Spacer(1, 15))

    # ---------------- SESSION TIMINGS ----------------
    content.append(Paragraph(
        "Forenoon Session (F.N) : 09.30 A.M. to 12.30 P.M.",
        normal_style
    ))

    content.append(Paragraph(
        "Afternoon Session (A.N) : 02.00 P.M. to 05.00 P.M.",
        normal_style
    ))

    content.append(Spacer(1, 12))

    # ---------------- INSTRUCTIONS ----------------
    content.append(Paragraph("<b>Instructions :</b>", normal_style))

    instructions = [
        "1) Be present at the control room atleast half an hour before the commencement of the Examination.",
        "2) Use of mobile phones is strictly prohibited during invigilation duty.",
        "3) Exchange or Transfer of duties will not be entertained without valid reasons and prior permission from the Principal."
    ]

    for inst in instructions:
        content.append(Paragraph(inst, normal_style))

    content.append(Spacer(1, 25))

    # ---------------- SIGNATURE ----------------
   
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    signature_path = os.path.join(BASE_DIR, "assets", "principal_sign.png")
    

    # ---------------- SIGNATURE ----------------
    if os.path.exists(signature_path):
        sign_img = Image(signature_path, width=120, height=50)
    else:
        sign_img = Paragraph("", normal_style)

    sign_table = Table([
        ["", sign_img],
        ["", Paragraph("<b>PRINCIPAL</b>", center_style)]
    ], colWidths=[350, 150])

    sign_table.setStyle(TableStyle([
        ("ALIGN", (1,0), (1,1), "RIGHT"),
    ]))

    content.append(sign_table)

    # ---------------- BUILD ----------------
    doc.build(content)

    return file

from sqlalchemy import text
import hashlib

def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()


def update_staff_credentials(staff_id, new_email, new_password):

    new_email = new_email.strip().lower()
    new_password = str(new_password).strip().zfill(5)
    hashed = hash_password(new_password)

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE staff
                SET email = :email,
                    bank_last5 = :password
                WHERE staff_id = :staff_id
            """),
            {
                "email": new_email,
                "password": hashed,
                "staff_id": staff_id
            }
        )

    return True
