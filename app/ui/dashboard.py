import streamlit as st
from datetime import datetime
from app.config import BUCKET_NAME, DANGER_LABELS, BODY_PART_LABELS
from app.rekognition import poll_dynamodb, save_data

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:378494867598:SecureGuard-Alerts"


def _get_stats(table):
    response = table.scan(ProjectionExpression="#st, Severity", ExpressionAttributeNames={"#st": "Status"})
    items = response.get('Items', [])
    total = len([i for i in items if i.get('Status') not in ('', None)])
    threats = len([i for i in items if i.get('Severity') in ('CRITICAL', 'MEDIUM')])
    authorized = len([i for i in items if i.get('Status') == 'AUTHORIZED'])
    return total, authorized, threats


def render_dashboard(rekognition, s3, table, sns):
    st.markdown('<h1 style="color:white;">🏠 SecureHome Dashboard</h1>', unsafe_allow_html=True)

    # --- STATS ROW ---
    total, authorized, threats_count = _get_stats(table)
    if total > 0:
        s1, s2, s3_col = st.columns(3)
        s1.metric("Total Scans", total)
        s2.metric("✅ Authorized", authorized)
        s3_col.metric("⛔ Threats / Alerts", threats_count)
        st.markdown("---")

    st.markdown('<p style="color:#00ffcc; font-size:1.5rem; font-weight:900; letter-spacing:2px;">📡 BIOMETRIC SCANNER — POSITION FACE IN FRAME</p>', unsafe_allow_html=True)
    col_cam, col_analysis = st.columns([1, 1.3], gap="large")

    with col_cam:
        img_file = st.camera_input("Scanner", label_visibility="collapsed")

    with col_analysis:
        if img_file:
            image_bytes = img_file.getvalue()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            capture_key = f"sec_capture_{ts.replace(' ', '_').replace(':', '')}.jpg"

            try:
                label_response = rekognition.detect_labels(
                    Image={'Bytes': image_bytes},
                    MaxLabels=st.session_state.get('max_labels', 20),
                    MinConfidence=50
                )
            except Exception as e:
                st.error(f"Rekognition error: {e}")
                st.stop()

            all_labels = [l['Name'] for l in label_response['Labels']]
            active_danger = DANGER_LABELS | set(st.session_state.get('custom_danger_labels', []))
            threats = [t for t in all_labels if t in active_danger]
            HUMAN_LABELS = {'Person', 'Human', 'Face', 'Head', 'Portrait', 'Selfie', 'People', 'Adult', 'Male', 'Female', 'Man', 'Woman', 'Boy', 'Girl', 'Child', 'Baby'}
            is_human = any(l in HUMAN_LABELS for l in all_labels)

            if threats:
                _show_threat(image_bytes, threats, ts, s3, sns, table, all_labels)
            elif is_human:
                _show_identity(image_bytes, ts, capture_key, s3, table, label_response)
            else:
                filtered = [l for l in label_response['Labels'] if l['Name'] not in BODY_PART_LABELS][:4]
                if filtered:
                    st.markdown('<p style="color:#aaaaaa; font-size:1.3rem; font-weight:800;">🔍 No person detected. Objects in frame:</p>', unsafe_allow_html=True)
                    i_col1, i_col2 = st.columns(2)
                    for idx, label in enumerate(filtered):
                        target = i_col1 if idx % 2 == 0 else i_col2
                        with target:
                            st.markdown(f'<div class="infra-card"><div class="infra-label">{label["Name"]}</div><div class="infra-val">{label["Confidence"]:.0f}% Confidence</div></div>', unsafe_allow_html=True)
                    try:
                        import time
                        table.put_item(Item={
                            'ImageId': capture_key,
                            'Timestamp': str(int(time.mktime(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').timetuple()))),
                            'Identity': 'No Face Detected',
                            'Status': 'GUEST_ACCESS',
                            'Severity': 'INFO',
                            'AlertStatus': 'New',
                            'MatchConfidence': 'N/A',
                            'TopEmotion': 'N/A',
                            'AgeRange': 'N/A',
                            'WearingHolding': [l['Name'] for l in label_response['Labels'] if l['Name'] not in BODY_PART_LABELS],
                            'DetectedLabels': [l['Name'] for l in label_response['Labels']],
                            'BucketSource': BUCKET_NAME
                        })
                    except Exception as e:
                        st.warning(f"Log error: {e}")
                else:
                    st.markdown('<p style="color:#aaaaaa; font-size:1.3rem; font-weight:800;">🔍 No person or objects detected. Please position in frame.</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#ffffff; font-size:1.8rem; font-weight:900; letter-spacing:1px;">⏳ Awaiting scanner input...</p>', unsafe_allow_html=True)


def _show_threat(image_bytes, threats, ts, s3, sns, table=None, all_labels=None):
    threat_str = ', '.join(threats).upper()
    st.markdown(f"""
    <div class="threat-card" style="background:#1a0000; border:2px solid #ff4444; border-radius:10px; padding:20px; margin-bottom:15px;">
        <p style="color:#ff4444; font-size:1.8rem; font-weight:900; margin:0;">🚨 SECURITY ALERT</p>
        <p style="color:#ffffff; font-size:1.3rem; font-weight:800; margin:8px 0 4px 0;">⚠️ Threat Detected: <span style="color:#ff4444;">{threat_str}</span></p>
        <p style="color:#aaaaaa; font-size:1.1rem; margin:4px 0;">📋 Reason: Dangerous object detected in secured zone</p>
        <p style="color:#ffaa00; font-size:1.1rem; font-weight:800; margin:4px 0;">🔒 Action: Access Denied — Notify security personnel immediately</p>
    </div>""", unsafe_allow_html=True)
    st.image(image_bytes, width=300)

    capture_key = f"threat_{ts.replace(' ', '_').replace(':', '')}.jpg"
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=capture_key, Body=image_bytes)
    except Exception as e:
        st.warning(f"S3 upload error: {e}")

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"🔴 SecureGuard CRITICAL Alert — {threat_str}",
            Message=f"Severity: CRITICAL\nTimestamp: {ts}\nThreat: {threat_str}\nIdentity: Unknown\n\nDangerous object detected in secured zone."
        )
    except Exception as e:
        st.warning(f"SNS error: {e}")

    if table:
        try:
            import time
            table.put_item(Item={
                'ImageId': capture_key,
                'Timestamp': str(int(time.mktime(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').timetuple()))),
                'Identity': 'Unknown / Threat',
                'Status': 'DENIED',
                'Severity': 'CRITICAL',
                'AlertStatus': '🔔 New',
                'DetectedLabels': threats,
                'WearingHolding': [l for l in (all_labels or []) if l not in BODY_PART_LABELS],
                'TopEmotion': 'N/A',
            })
        except Exception as e:
            st.warning(f"DynamoDB write error: {e}")


def _show_identity(image_bytes, ts, capture_key, s3, table, label_response):
    with st.spinner("📡 Uploading to S3... triggering identity verification..."):
        s3.put_object(Bucket=BUCKET_NAME, Key=capture_key, Body=image_bytes)

    with st.spinner("🔍 Waiting for identity match result from Lambda..."):
        result = poll_dynamodb(table, capture_key)

    if result:
        identity = result.get("Identity", "Unknown")
        emotion = result.get("TopEmotion", "N/A")
        age_range = result.get("AgeRange", "N/A")
        is_verified = result.get("Status") == "AUTHORIZED"

        if identity == "Spoof Attempt":
            st.markdown("""
            <div style="background:#1a0a00; border:2px solid #ff8800; border-radius:10px; padding:20px; margin-bottom:15px;">
                <p style="color:#ff8800; font-size:1.8rem; font-weight:900; margin:0;">🎭 SPOOF DETECTED</p>
                <p style="color:#ffffff; font-size:1.3rem; font-weight:800; margin:8px 0 4px 0;">📵 Photo or screen detected — not a live face</p>
                <p style="color:#aaaaaa; font-size:1.1rem; margin:4px 0;">📋 Reason: Image appears to be a photo, phone, or printed picture</p>
                <p style="color:#ffaa00; font-size:1.1rem; font-weight:800; margin:4px 0;">🔒 Action: Access Denied — Present your real face</p>
            </div>""", unsafe_allow_html=True)
            st.image(image_bytes, width=300)
        elif is_verified:
            name = identity.replace(" (Team Member)", "")
            st.markdown(f"""
            <div style="background:#001a0e; border:2px solid #00ffcc; border-radius:10px; padding:20px; margin-bottom:15px;">
                <p style="color:#00ffcc; font-size:1.8rem; font-weight:900; margin:0;">✅ IDENTITY VERIFIED</p>
                <p style="color:#ffffff; font-size:1.3rem; font-weight:800; margin:8px 0 4px 0;">👤 User: <span style="color:#00ffcc;">{name.upper()}</span></p>
                <p style="color:#aaaaaa; font-size:1.1rem; margin:4px 0;">📋 Reason: Face matched against registered identity database</p>
                <p style="color:#00ffcc; font-size:1.1rem; font-weight:800; margin:4px 0;">🔓 Action: Access Granted — Welcome, {name}</p>
            </div>""", unsafe_allow_html=True)
            st.image(image_bytes, width=300)
            m1, m2 = st.columns(2)
            m1.metric("Emotion", emotion)
            m2.metric("Status", "✅ VERIFIED")

            filtered = [l for l in label_response['Labels'] if l['Name'] not in BODY_PART_LABELS][:4]
            if filtered:
                st.markdown('<p style="color:white; font-weight:bold; font-size:1.2rem;">🔍 Scene Analysis</p>', unsafe_allow_html=True)
                i_col1, i_col2 = st.columns(2)
                for idx, label in enumerate(filtered):
                    target = i_col1 if idx % 2 == 0 else i_col2
                    with target:
                        st.markdown(f'<div class="infra-card"><div class="infra-label">{label["Name"]}</div><div class="infra-val">{label["Confidence"]:.0f}% Match</div></div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="threat-card" style="background:#1a0000; border:2px solid #ff4444; border-radius:10px; padding:20px; margin-bottom:15px;">
                <p style="color:#ff4444; font-size:1.8rem; font-weight:900; margin:0;">🚫 UNKNOWN PERSON</p>
                <p style="color:#ffffff; font-size:1.3rem; font-weight:800; margin:8px 0 4px 0;">👤 No match found in registry</p>
                <p style="color:#aaaaaa; font-size:1.1rem; margin:4px 0;">📋 Reason: Face does not match any registered identity</p>
                <p style="color:#ffaa00; font-size:1.1rem; font-weight:800; margin:4px 0;">🔒 Action: Access Denied — Unrecognized individual</p>
            </div>""", unsafe_allow_html=True)
            st.image(image_bytes, width=300)
    else:
        st.warning("⏳ Lambda did not respond in time. Please try again.")
