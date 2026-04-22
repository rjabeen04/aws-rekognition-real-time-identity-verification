import streamlit as st
from PIL import Image, ImageOps
import io
from app.config import BUCKET_NAME

COLLECTION_ID = "secureguard-users"


def render_registry(s3, table_registry, rekognition_client=None):
    st.markdown('<h2 style="color:white;">👥 Identity Registry</h2>', unsafe_allow_html=True)
    st.markdown("---")

    # --- FETCH RESIDENTS ---
    try:
        response = table_registry.scan()
        residents = response.get('Items', [])
    except Exception as e:
        st.error(f"Failed to load registry: {e}")
        return

    if residents:
        col_count, col_export = st.columns([3, 1])
        with col_count:
            st.markdown(f'<p style="color:#00ffcc; font-size:1.2rem; font-weight:900;">{len(residents)} registered user(s)</p>', unsafe_allow_html=True)
        with col_export:
            import pandas as pd
            registry_df = pd.DataFrame([{
                'Name': r.get('Name'),
                'Clearance': r.get('Clearance'),
                'Relationship': r.get('Relationship'),
                'Address': r.get('Address'),
                'Phone': r.get('Phone'),
                'Status': r.get('Status')
            } for r in residents])
            csv = registry_df.to_csv(index=False)
            st.download_button("⬇️ Export Registry CSV", csv, "registry.csv", "text/csv", type="primary", key="registry_export")

        # Scrollable container
        scroll_html = ""
        for resident in residents:
            clearance_color = "#ff4444" if resident.get('Clearance') == "Admin" else "#ffaa00" if resident.get('Clearance') == "Team Member" else "#00ffcc"
            try:
                img_obj = s3.get_object(Bucket=BUCKET_NAME, Key=resident['ImageKey'])
                img_bytes = img_obj['Body'].read()
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img)
                img.thumbnail((60, 60))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                import base64
                img_b64 = base64.b64encode(buf.getvalue()).decode()
                img_tag = f'<img src="data:image/jpeg;base64,{img_b64}" style="width:60px; height:60px; object-fit:cover; border-radius:50%; border:2px solid #00ffcc;">'
            except Exception:
                img_tag = '<img src="https://ui-avatars.com/api/?name={name}&background=1a1a2e&color=00ffcc&size=60&rounded=true&bold=true" style="width:60px; height:60px; border-radius:50%; border:2px solid #555;">'.format(name=resident.get('Name', 'U').replace(' ', '+'))

            scroll_html += f"""
            <div style="display:flex; align-items:center; padding:14px; border-bottom:1px solid #1e2a1e; gap:16px;">
                {img_tag}
                <div style="flex:1;">
                    <p style="color:#00ffcc; font-size:1.4rem; font-weight:900; margin:0;">{resident.get('Name', '').upper()}</p>
                    <p style="color:{clearance_color}; font-size:1.1rem; font-weight:800; margin:4px 0;">🔐 {resident.get('Clearance', 'N/A')} &nbsp;|&nbsp; 👤 {resident.get('Relationship', 'N/A')} &nbsp;|&nbsp; ✅ {resident.get('Status', 'Active')}</p>
                    <p style="color:#cccccc; font-size:1rem; font-weight:600; margin:0;">📍 {resident.get('Address', 'N/A')} &nbsp;|&nbsp; 📞 {resident.get('Phone', 'N/A')}</p>
                </div>
            </div>"""

        st.markdown(f'<div style="max-height:400px; overflow-y:auto; border:1px solid #30363d; border-radius:8px; background:#0d1117;">{scroll_html}</div>', unsafe_allow_html=True)

        # Delete section below scroll
        st.markdown('<p style="color:#ffffff; font-size:1.2rem; font-weight:900; margin-top:12px;">🗑️ Remove a resident:</p>', unsafe_allow_html=True)
        resident_names = {r['Name']: r['ResidentId'] for r in residents}
        selected = st.selectbox("Select resident to remove", ["-- Select --"] + list(resident_names.keys()), label_visibility="collapsed")
        if st.button("🗑️ Remove Selected", type="primary"):
            if selected != "-- Select --":
                st.session_state["confirm_delete"] = selected

        if st.session_state.get("confirm_delete") and st.session_state["confirm_delete"] != "-- Select --":
            st.warning(f"Remove **{st.session_state['confirm_delete']}**?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Remove", type="primary", key="confirm_yes"):
                    table_registry.delete_item(Key={'ResidentId': resident_names[st.session_state['confirm_delete']]})
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", key="confirm_no"):
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
    else:
        st.markdown('<p style="color:#aaaaaa;">No residents found.</p>', unsafe_allow_html=True)

    st.markdown("---")

    # --- ADD NEW RESIDENT FORM ---
    st.markdown('<p style="color:#00ffcc; font-size:1.3rem; font-weight:900;">➕ Add New Resident</p>', unsafe_allow_html=True)
    st.markdown("""
    <style>
    .stTextInput input { font-size:1.1rem !important; padding: 8px 12px !important; }
    .stSelectbox div[data-baseweb="select"] { font-size:1.1rem !important; }
    .stForm label p { font-size:1.2rem !important; font-weight:800 !important; color:#ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

    form_col, _ = st.columns([1.5, 1])
    with form_col:
        with st.form("add_resident_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("Full Name *")
                clearance = st.selectbox("Clearance Level", ["Resident", "Admin", "Team Member", "Guest", "Family", "Friend"])
            with col2:
                relationship = st.selectbox("Relationship", ["Resident", "Family", "Friend", "Guest", "Team Member"])
                address = st.text_input("Address")
            with col3:
                phone = st.text_input("Phone")
                status = st.selectbox("Status", ["Active", "Inactive"])

            photo = st.file_uploader("Upload Reference Photo *", type=["jpg", "jpeg", "png"])
            submitted = st.form_submit_button("💾 Save Resident", type="primary")

            if submitted:
                if not name or not photo:
                    st.error("Name and photo are required.")
                else:
                    resident_id = name.lower().replace(" ", "_")
                    image_key = f"{resident_id}.jpg"
                    try:
                        img = Image.open(photo)
                        img = ImageOps.exif_transpose(img)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG")
                        buf.seek(0)
                        s3.put_object(Bucket=BUCKET_NAME, Key=image_key, Body=buf.getvalue())
                    except Exception as e:
                        st.error(f"Photo upload failed: {e}")
                        return
                    # Index face into Rekognition collection
                    if rekognition_client:
                        try:
                            rekognition_client.index_faces(
                                CollectionId=COLLECTION_ID,
                                Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': image_key}},
                                ExternalImageId=name,
                                DetectionAttributes=['DEFAULT']
                            )
                        except Exception as e:
                            st.warning(f"Face indexing failed: {e}")
                    try:
                        table_registry.put_item(Item={
                            'ResidentId': resident_id,
                            'Name': name,
                            'ImageKey': image_key,
                            'Clearance': clearance,
                            'Relationship': relationship,
                            'Address': address or 'N/A',
                            'Phone': phone or 'N/A',
                            'Status': status
                        })
                        st.success(f"✅ {name} added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
