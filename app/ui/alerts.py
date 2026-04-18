import streamlit as st
import pandas as pd
from datetime import datetime
from app.ui.styles import render_table
from app.config import DANGER_LABELS
import boto3


def get_severity(threats):
    threat_list = [t.strip() for t in threats.split(",")]
    if any(t in DANGER_LABELS for t in threat_list):
        return "🔴 CRITICAL"
    if "Unknown" in threats or "Guest" in threats:
        return "🟡 MEDIUM"
    return "🔵 INFO"


def fetch_alerts(table):
    response = table.scan()
    items = response.get('Items', [])
    alerts = []
    for item in items:
        identity = item.get('Identity', '')
        severity = item.get('Severity', '')
        is_threat = severity == 'CRITICAL' or 'Threat' in identity
        is_unknown = severity == 'MEDIUM' and 'Unknown' in identity
        if not (is_threat or is_unknown):
            continue
        if identity in ('No Face Detected', None, ''):
            continue
        ts = item.get('Timestamp', '')
        try:
            ts = datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        labels = item.get('DetectedLabels', [])
        threats = ', '.join([l for l in labels if l in DANGER_LABELS]) or ('Unknown Person' if 'Unknown' in identity else identity)
        alerts.append({
            'Timestamp': ts,
            'Threats': threats,
            'Severity': severity,
            'AlertStatus': item.get('AlertStatus', '🔔 New'),
            'ImageId': item.get('ImageId', '')
        })
    return sorted(alerts, key=lambda x: x['Timestamp'], reverse=True)


def render_alerts(table):
    st.markdown('<h2 style="color:white;">🔔 Security Alerts</h2>', unsafe_allow_html=True)
    alerts = fetch_alerts(table)
    if alerts:
        csv = pd.DataFrame(alerts).to_csv(index=False)
        st.download_button("⬇️ Export Alerts CSV", csv, "alerts.csv", "text/csv", type="primary", key="alerts_download")

        rows = []
        for a in alerts:
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
            alert_idx = st.selectbox("Select Alert", range(len(alerts)),
                format_func=lambda i: f"{alerts[i]['Timestamp']} — {alerts[i]['Threats'][:30]}",
                label_visibility="collapsed")
        with col2:
            new_status = st.selectbox("New Status", ["🔔 New", "👀 Acknowledged", "✅ Resolved"], label_visibility="collapsed")
        with col3:
            if st.button("Update", type="primary"):
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                dynamodb.Table('ImageAnalysisResults').update_item(
                    Key={'ImageId': alerts[alert_idx]['ImageId'], 'Timestamp': str(int(datetime.strptime(alerts[alert_idx]['Timestamp'], '%Y-%m-%d %H:%M:%S').timestamp()))},
                    UpdateExpression='SET AlertStatus = :s',
                    ExpressionAttributeValues={':s': new_status}
                )
                st.rerun()
    else:
        st.markdown('<p style="color:#aaaaaa; font-size:1.2rem;">No alerts recorded yet.</p>', unsafe_allow_html=True)
