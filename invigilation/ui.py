import streamlit as st


def apply_ui():

    st.markdown("""
    <style>

    @media (prefers-color-scheme: light) {
        .card {
            background:#1e1e1e;
            color:#fff;
            padding:25px;
            border-radius:15px;
            margin-top:20px;
            box-shadow:0 4px 12px rgba(0,0,0,0.2);
        }
        .duty-card {
            background:#2b2b2b;
            color:#fff;
            padding:15px;
            border-radius:10px;
            margin:10px 0;
            border-left:5px solid #4CAF50;
        }
    }

    @media (prefers-color-scheme: dark) {
        .card {
            background:#fff;
            color:#000;
            padding:25px;
            border-radius:15px;
            margin-top:20px;
            box-shadow:0 4px 12px rgba(0,0,0,0.1);
        }
        .duty-card {
            background:#f5f5f5;
            color:#000;
            padding:15px;
            border-radius:10px;
            margin:10px 0;
            border-left:5px solid #4CAF50;
        }
    }

    .title {
        text-align:center;
        font-size:32px;
        font-weight:700;
    }

    .subtitle {
        text-align:center;
        opacity:0.7;
        margin-bottom:20px;
    }
    .card:empty {
    display: none;
    }
    
    .card:hover {
    transform: translateY(-3px);
    transition: 0.2s ease;
    }
    
    /* Stats cards */
    .stat-card {
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    margin: 5px;
    font-weight: bold;
    }

/* Light Mode */
    @media (prefers-color-scheme: light) {
    .stat-card { background: #2b2b2b; color: white; }
    .fn { border-left: 5px solid #4CAF50; }
    .an { border-left: 5px solid #2196F3; }
    .other { border-left: 5px solid #9C27B0; }
    }

/* Dark Mode */
    @media (prefers-color-scheme: dark) {
    .stat-card { background: #f5f5f5; color: black; }
    .fn { border-left: 5px solid #4CAF50; }
    .an { border-left: 5px solid #2196F3; }
    .other { border-left: 5px solid #9C27B0; }
    }

    </style>
    """, unsafe_allow_html=True)