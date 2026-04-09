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
def process_excel(file):
    staff_df = pd.read_excel(file, sheet_name="Staff")
    duty_df = pd.read_excel(file, sheet_name="duty")

    # CLEAN STAFF DATA
    staff_df = staff_df.rename(columns={
        "ID": "staff_id",
        "Name": "name",
        "Dept": "dept",
        "email": "email",
        "bank_last5": "bank_last5"
    })

    staff_df["email"] = staff_df["email"].astype(str).str.strip().str.lower()
    staff_df["bank_last5"] = staff_df["bank_last5"].astype(str).str.strip()

    # Hash safely
    staff_df["bank_last5"] = staff_df["bank_last5"].apply(
        lambda x: hash_password(x) if len(x) < 20 else x
    )

    staff_df = staff_df[["staff_id", "name", "dept", "email", "bank_last5"]]

    # CLEAN DUTY DATA
    duty_df = duty_df.rename(columns={
        "ID": "staff_id",
        "Session": "session_text",
        "order": "duty_order"
    })

    duty_df = duty_df[["staff_id", "session_text", "duty_order"]]

    # SAFE INSERT (NO TABLE DROP)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staff"))
        conn.execute(text("DELETE FROM duty"))

    staff_df.to_sql("staff", engine, if_exists="append", index=False)
    duty_df.to_sql("duty", engine, if_exists="append", index=False)
