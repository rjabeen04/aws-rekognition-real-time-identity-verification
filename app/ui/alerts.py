import streamlit as st
import pandas as pd
from app.ui.styles import render_table
from app.rekognition import save_data


def get_severity(threats):
    critical = {"Knife", "Gun", "Weapon", "Rifle", "Pistol"}
    threat_list = [t.strip() for t in threats.split(",")]
    if any(t in critical for t in threat_list):
        return "🔴 CRITICAL"
    if "Unknown Person" in threats:
        return "🟡 MEDIUM"
    return "🔵 INFO"


def render_alerts():
    st.markdown('<h2 style="color:white;">🔔 Security Alerts</h2>', unsafe_allow_html=True)
    if st.session_state.alerts:
        csv = pd.DataFrame(st.session_state.alerts).to_csv(index=False)
        st.download_button("⬇️ Export Alerts CSV", csv, "alerts.csv", "text/csv", type="primary", key="alerts_download")

        rows = []
        for idx, a in enumerate(reversed(st.session_state.alerts)):
            severity = get_severity(a['Threats'])
            alert_status = a.get('AlertStatus', '🔔 New')
            severity_color = "#ff4444" if "CRITICAL" in severity else "#ffaa00" if "MEDIUM" in severity else "#4488ff"
            status_color = "#aaaaaa" if "New" in alert_status else "#ffaa00" if "Acknowledged" in alert_status else "#00ffcc"
            rows.append(f"""<tr style="border-bottom:1px solid #30363d;">
                <td style="padding:14px; color:{severity_color}; font-size:1.2rem; font-weight:900;">{severity}</td>
                <td style="padding:14px; color:#ffffff; font-size:1.2rem; font-weight:800;">{a['Timestamp']}</td>
                <td style="padding:14px; color:#ff4444; font-size:1.2rem; font-weight:900;">{a['Threats'].upper()}</td>
                <td style="padding:14px; color:{status_color}; font-size:1.1rem; font-weight:800;">{alert_status}</td>
            </tr>""")
        render_table("".join(rows), ["Severity", "Timestamp", "Threat Type", "Status"])

        st.markdown("---")
        st.markdown('<p style="color:#ffffff; font-size:1.1rem; font-weight:800;">Update Alert Status:</p>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            alert_idx = st.selectbox("Select Alert", range(len(st.session_state.alerts)),
                format_func=lambda i: f"{st.session_state.alerts[i]['Timestamp']} — {st.session_state.alerts[i]['Threats'][:30]}",
                label_visibility="collapsed")
        with col2:
            new_status = st.selectbox("New Status", ["🔔 New", "👀 Acknowledged", "✅ Resolved"], label_visibility="collapsed")
        with col3:
            if st.button("Update", type="primary"):
                st.session_state.alerts[alert_idx]['AlertStatus'] = new_status
                save_data()
                st.rerun()
    else:
        st.markdown('<p style="color:#aaaaaa; font-size:1.2rem;">No alerts recorded yet.</p>', unsafe_allow_html=True)
