import streamlit as st


def apply_styles():
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px; background-color: #0d1117; padding: 10px 20px;
        border-radius: 10px 10px 0 0; border-bottom: 2px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] { padding: 18px 36px !important; }
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] button {
        font-size: 1.5rem !important; font-weight: 900 !important;
        color: #ffffff !important; letter-spacing: 2px !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] div,
    .stTabs [data-baseweb="tab"][aria-selected="true"] span,
    .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    .stTabs [data-baseweb="tab"][aria-selected="true"] button {
        color: #00ffcc !important; text-shadow: 0 0 12px #00ffcc !important;
    }
    .infra-card {
        background-color: #080a0c; border: 1px solid #00ffcc;
        padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 15px;
    }
    .infra-label { color: #00ffcc !important; font-weight: 900; text-transform: uppercase; font-size: 1.2rem; letter-spacing: 1px; }
    .infra-val { color: #ffffff !important; font-size: 1.1rem; font-weight: 700; margin-top: 6px; }
    [data-testid="stMetricLabel"] p { font-size: 1.2rem !important; color: #ffffff !important; font-weight: 800; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 900; color: #00ffcc !important; }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255,68,68,0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255,68,68,0); }
        100% { box-shadow: 0 0 0 0 rgba(255,68,68,0); }
    }
    .threat-card { animation: pulse-red 1.5s infinite; }
    [data-testid="stCameraInputButton"] {
        background-color: #00ffcc !important; color: #000000 !important;
        font-size: 1.2rem !important; font-weight: 900 !important;
        border-radius: 8px !important; padding: 12px 24px !important;
        letter-spacing: 2px !important; border: none !important;
    }
    [data-testid="stCameraInputButton"]::after { content: "🔍 SCAN NOW"; }
    [data-testid="stCameraInputButton"] span { display: none; }
    </style>
    """, unsafe_allow_html=True)


def render_table(rows_html, headers):
    header_cells = "".join(
        f'<th style="padding:14px; color:#00ffcc; font-size:1.2rem; text-align:left; text-transform:uppercase; letter-spacing:1px;">{h}</th>'
        for h in headers
    )
    st.markdown(
        f'<table style="width:100%; border-collapse:collapse;"><tr style="border-bottom:2px solid #30363d;">{header_cells}</tr>{rows_html}</table>',
        unsafe_allow_html=True
    )
