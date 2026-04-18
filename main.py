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

# --- AWS CLIENTS (cached across reruns) ---
rekognition, s3, table, table_registry, sns = init_clients()

# --- SESSION STATE ---
if "alerts" not in st.session_state:
    data = load_data()
    st.session_state.alerts = data["alerts"]
    st.session_state.logs = data["logs"]
    settings = data.get("settings", {})
    st.session_state.similarity_threshold = settings.get("similarity_threshold", 80)
    st.session_state.max_labels = settings.get("max_labels", 15)
    st.session_state.custom_danger_labels = settings.get("custom_danger_labels", [])
elif not st.session_state.alerts and not st.session_state.logs:
    data = load_data()
    st.session_state.alerts = data["alerts"]
    st.session_state.logs = data["logs"]

# --- TABS ---
tab_dash, tab_alerts, tab_logs, tab_registry, tab_settings = st.tabs([
    "📊 DASHBOARD", "🔔 ALERTS", "📋 LOGS", "👥 REGISTRY", "⚙️ SETTINGS"
])

with tab_dash:
    render_dashboard(rekognition, s3, table, sns)

with tab_alerts:
    render_alerts()

with tab_logs:
    render_logs()

with tab_registry:
    render_registry(s3, table_registry)

with tab_settings:
    render_settings()
