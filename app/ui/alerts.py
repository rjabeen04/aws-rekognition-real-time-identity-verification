import streamlit as st
import pandas as pd
from app.ui.styles import render_table


def render_alerts():
    st.markdown('<h2 style="color:white;">🔔 Security Alerts</h2>', unsafe_allow_html=True)
    if st.session_state.alerts:
        csv = pd.DataFrame(st.session_state.alerts).to_csv(index=False)
        st.download_button("⬇️ Export Alerts CSV", csv, "alerts.csv", "text/csv", use_container_width=False, type="primary", key="alerts_download")
        rows = []
        for a in reversed(st.session_state.alerts):
            rows.append(f"""<tr style="border-bottom:1px solid #30363d;">
                <td style="padding:14px; color:#ffffff; font-size:1.2rem; font-weight:800;">{a['Timestamp']}</td>
                <td style="padding:14px; color:#ff4444; font-size:1.2rem; font-weight:900;">{a['Threats'].upper()}</td>
                <td style="padding:14px; color:#aaaaaa; font-size:1.1rem; font-weight:700;">{a['Top Label']}</td>
            </tr>""")
        render_table("".join(rows), ["Timestamp", "Threats", "Top Label"])
    else:
        st.markdown('<p style="color:#aaaaaa; font-size:1.2rem;">No alerts recorded yet.</p>', unsafe_allow_html=True)
