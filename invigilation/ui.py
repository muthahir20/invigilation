import streamlit as st

def apply_ui():
    st.markdown("""
    <style>

    /* Main App */
    .stApp {
        font-family: 'Segoe UI', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        color: white;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Titles */
    .title {
        text-align:center;
        font-size:36px;
        font-weight:700;
    }

    .subtitle {
        text-align:center;
        opacity:0.7;
        margin-bottom:25px;
    }

    /* Cards */
    .card {
        padding: 25px;
        border-radius: 16px;
        background: #1f2937;
        color: white;
        box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    }

    /* Duty Card */
    .duty-card {
        background:#1f2937;
        color:white;
        padding:14px;
        border-radius:10px;
        margin:10px 0;
        border-left:5px solid #4CAF50;
    }

    /* Stat Cards */
    .stat-card {
        padding: 20px;
        border-radius: 14px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: white;
    }

    .fn { background: #16a34a; }
    .an { background: #2563eb; }
    .other { background: #9333ea; }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
    }
    /* Input styling */
    input {
    border-radius: 10px !important;
    padding: 10px !important;
    }
    .card:empty {
    display: none;
    }
                /* Duty color coding */
    .duty-card.fn {
        border-left: 5px solid #22c55e;  /* green */
    }

    .duty-card.an {
        border-left: 5px solid #3b82f6;  /* blue */
    }

    .duty-card.other {
        border-left: 5px solid #a855f7;  /* purple */
    }

    </style>
    """, unsafe_allow_html=True)
