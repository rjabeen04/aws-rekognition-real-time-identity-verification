import streamlit as st
import pandas as pd
from app.ui.styles import render_table


def render_logs():
    st.markdown('<h2 style="color:white;">📋 Access History</h2>', unsafe_allow_html=True)
    if st.session_state.logs:
        csv = pd.DataFrame(st.session_state.logs).to_csv(index=False)
        st.download_button("⬇️ Export Logs CSV", csv, "access_logs.csv", "text/csv", use_container_width=False, type="primary", key="logs_download")
        rows = ""
        for log in reversed(st.session_state.logs):
            status_color = "#00ffcc" if "AUTHORIZED" in log["Status"] else "#ff4444"
            rows += f"""<tr style="border-bottom:1px solid #30363d;">
                <td style="padding:14px; color:#ffffff; font-size:1.2rem; font-weight:800;">{log['Timestamp']}</td>
                <td style="padding:14px; color:#ffffff; font-size:1.2rem; font-weight:800;">{log.get('User', 'N/A')}</td>
                <td style="padding:14px; color:{status_color}; font-size:1.2rem; font-weight:900;">{log['Status']}</td>
                <td style="padding:14px; color:#00ffcc; font-size:1.1rem; font-weight:700;">{log.get('MatchConfidence', 'N/A')}</td>
                <td style="padding:14px; color:#aaaaaa; font-size:1.1rem; font-weight:700;">{log.get('Emotion', 'N/A')}</td>
                <td style="padding:14px; color:#aaaaaa; font-size:1.1rem; font-weight:700;">{log.get('WearingHolding', 'N/A')}</td>
                <td style="padding:14px; color:#555555; font-size:0.95rem;">{log.get('ImageKey', 'N/A')}</td>
            </tr>"""
        render_table(rows, ["Timestamp", "Name", "Status", "Match %", "Emotion", "Scene Objects", "Image Key"])
    else:
        st.markdown('<p style="color:#aaaaaa; font-size:1.2rem;">No scans recorded yet.</p>', unsafe_allow_html=True)
