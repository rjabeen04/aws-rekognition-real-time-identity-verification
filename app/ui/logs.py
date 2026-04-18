import streamlit as st
import pandas as pd
from datetime import datetime
from app.ui.styles import render_table


def fetch_logs(table):
    response = table.scan()
    items = response.get('Items', [])
    logs = []
    for item in items:
        identity = item.get('Identity', 'N/A')
        status = item.get('Status', 'N/A')
        if identity in ('No Face Detected', None) or status == 'COMPLETED':
            continue
        ts = item.get('Timestamp', '')
        try:
            ts = datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        logs.append({
            'Timestamp': ts,
            'User': identity.replace(' (Team Member)', ''),
            'Status': '✅ AUTHORIZED' if status == 'AUTHORIZED' else '⛔ DENIED',
            'Match %': item.get('MatchConfidence', 'N/A'),
            'Emotion': item.get('TopEmotion', 'N/A'),
            'Scene Objects': ', '.join(item.get('WearingHolding', [])),
            'Image Key': item.get('ImageId', 'N/A')
        })
    return sorted(logs, key=lambda x: x['Timestamp'], reverse=True)


def render_logs(table):
    st.markdown('<h2 style="color:white;">📋 Access History</h2>', unsafe_allow_html=True)
    logs = fetch_logs(table)
    if logs:
        csv = pd.DataFrame(logs).to_csv(index=False)
        st.download_button("⬇️ Export Logs CSV", csv, "access_logs.csv", "text/csv", type="primary", key="logs_download")
        rows = []
        for log in logs:
            status_color = "#00ffcc" if "AUTHORIZED" in log["Status"] else "#ff4444"
            rows.append(f"""<tr style="border-bottom:1px solid #30363d;">
                <td style="padding:14px; color:#ffffff; font-size:1.2rem; font-weight:800;">{log['Timestamp']}</td>
                <td style="padding:14px; color:#ffffff; font-size:1.2rem; font-weight:800;">{log['User']}</td>
                <td style="padding:14px; color:{status_color}; font-size:1.2rem; font-weight:900;">{log['Status']}</td>
                <td style="padding:14px; color:#00ffcc; font-size:1.1rem; font-weight:700;">{log['Match %']}</td>
                <td style="padding:14px; color:#aaaaaa; font-size:1.1rem; font-weight:700;">{log['Emotion']}</td>
                <td style="padding:14px; color:#aaaaaa; font-size:1.1rem; font-weight:700;">{log['Scene Objects']}</td>
                <td style="padding:14px; color:#555555; font-size:0.95rem;">{log['Image Key']}</td>
            </tr>""")
        render_table("".join(rows), ["Timestamp", "Name", "Status", "Match %", "Emotion", "Scene Objects", "Image Key"])
    else:
        st.markdown('<p style="color:#aaaaaa; font-size:1.2rem;">No scans recorded yet.</p>', unsafe_allow_html=True)
