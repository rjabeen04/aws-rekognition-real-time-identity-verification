import streamlit as st
from app.aws_clients import init_clients
from app.rekognition import load_data
from app.ui.styles import apply_styles
from app.ui.dashboard import render_dashboard
from app.ui.alerts import render_alerts
from app.ui.logs import render_logs
from app.ui.registry import render_registry
from app.ui.settings import render_settings

# --- CONFIG ---
st.set_page_config(page_title="SecureHome AI", layout="wide")

# --- STYLES ---
apply_styles()

# --- AWS CLIENTS (only init once) ---
if "aws_ready" not in st.session_state:
    st.session_state.rekognition, st.session_state.s3, st.session_state.table = init_clients()
    st.session_state.aws_ready = True

# --- SESSION STATE ---
if "alerts" not in st.session_state:
    data = load_data()
    st.session_state.alerts = data["alerts"]
    st.session_state.logs = data["logs"]
elif not st.session_state.alerts and not st.session_state.logs:
    data = load_data()
    st.session_state.alerts = data["alerts"]
    st.session_state.logs = data["logs"]

# --- TABS ---
tab_dash, tab_alerts, tab_logs, tab_registry, tab_settings = st.tabs([
    "📊 DASHBOARD", "🔔 ALERTS", "📋 LOGS", "👥 REGISTRY", "⚙️ SETTINGS"
])

with tab_dash:
    render_dashboard(st.session_state.rekognition, st.session_state.s3, st.session_state.table)

with tab_alerts:
    render_alerts()

with tab_logs:
    render_logs()

with tab_registry:
    render_registry(st.session_state.s3)

with tab_settings:
    render_settings()
