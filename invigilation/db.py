from sqlalchemy import create_engine, text
import pandas as pd
import hashlib
import streamlit as st

USERNAME = st.secrets["DB_USERNAME"]
PASSWORD = st.secrets["DB_PASSWORD"]
HOST = st.secrets["DB_HOST"]
PORT = st.secrets["DB_PORT"]
DATABASE = st.secrets["DB_NAME"]

engine = create_engine(
    f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    "?ssl_verify_cert=false&ssl_verify_identity=false"
)

def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def staff_login(email, password):
    hashed = hash_password(password)

    query = text("""
        SELECT staff_id, name, dept
        FROM staff 
        WHERE email = :email AND bank_last5 = :password
    """)

    with engine.connect() as conn:
        return conn.execute(query, {"email": email, "password": hashed}).fetchone()

def admin_login(username, password):
    hashed = hash_password(password)

    query = text("""
        SELECT id, role FROM admin_users
        WHERE username = :username AND password = :password
    """)

    with engine.connect() as conn:
        return conn.execute(query, {
            "username": username,
            "password": hashed
        }).fetchone()

def get_duties(staff_id):
    query = text("""
        SELECT session_text, duty_order
        FROM duty
        WHERE staff_id = :staff_id
        ORDER BY duty_order
    """)

    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"staff_id": staff_id})

def process_excel(file):
    staff_df = pd.read_excel(file, sheet_name="Staff ")
    duty_df = pd.read_excel(file, sheet_name="duty")

    staff_df = staff_df.rename(columns={
        "ID": "staff_id",
        "Name": "name",
        "Dept": "dept",
        "email": "email",
        "bank_last5": "bank_last5"
    })

    staff_df["bank_last5"] = staff_df["bank_last5"].apply(hash_password)
    staff_df = staff_df[["staff_id", "name", "dept", "email", "bank_last5"]]

    duty_df = duty_df.rename(columns={
        "ID": "staff_id",
        "Session": "session_text",
        "order": "duty_order"
    })

    duty_df = duty_df[["staff_id", "session_text", "duty_order"]]

    staff_df.to_sql("staff", engine, if_exists="replace", index=False)
    duty_df.to_sql("duty", engine, if_exists="replace", index=False)