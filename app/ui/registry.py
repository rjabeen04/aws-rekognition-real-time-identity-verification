import streamlit as st
from PIL import Image, ImageOps
import io
from app.config import BUCKET_NAME


def render_registry(s3, table_registry):
    st.markdown('<h2 style="color:white;">👥 Identity Registry</h2>', unsafe_allow_html=True)
    st.markdown("---")

    # --- EXISTING RESIDENTS ---
    try:
        response = table_registry.scan()
        residents = response.get('Items', [])
    except Exception as e:
        st.error(f"Failed to load registry: {e}")
        return

    if residents:
        cols = st.columns(min(len(residents), 4))
        for idx, resident in enumerate(residents):
            with cols[idx % 4]:
                try:
                    img_obj = s3.get_object(Bucket=BUCKET_NAME, Key=resident['ImageKey'])
                    img_bytes = img_obj['Body'].read()
                    img = Image.open(io.BytesIO(img_bytes))
                    img = ImageOps.exif_transpose(img)
                    st.image(img, width=180)
                except Exception:
                    st.markdown('<p style="color:#ff4444;">No image</p>', unsafe_allow_html=True)

                clearance_color = "#ff4444" if resident.get('Clearance') == "Admin" else "#ffaa00" if resident.get('Clearance') == "Team Member" else "#00ffcc"
                st.markdown(f"""
                <div style="background:#001a0e; border:1px solid #00ffcc; border-radius:8px; padding:12px; text-align:center; margin-top:8px; margin-bottom:16px;">
                    <p style="color:#00ffcc; font-size:1.2rem; font-weight:900; margin:0;">{resident.get('Name', '').upper()}</p>
                    <p style="color:{clearance_color}; font-size:0.95rem; font-weight:700; margin:4px 0;">🔐 {resident.get('Clearance', 'N/A')}</p>
                    <p style="color:#aaaaaa; font-size:0.9rem; margin:2px 0;">👤 {resident.get('Relationship', 'N/A')}</p>
                    <p style="color:#aaaaaa; font-size:0.9rem; margin:2px 0;">📍 {resident.get('Address', 'N/A')}</p>
                    <p style="color:#00ffcc; font-size:0.9rem; font-weight:700; margin:2px 0;">✅ {resident.get('Status', 'Active')}</p>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#aaaaaa;">No residents found.</p>', unsafe_allow_html=True)

    st.markdown("---")

    # --- ADD NEW RESIDENT FORM ---
    st.markdown('<p style="color:#00ffcc; font-size:1.3rem; font-weight:900;">➕ Add New Resident</p>', unsafe_allow_html=True)

    with st.form("add_resident_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            clearance = st.selectbox("Clearance Level", ["Resident", "Admin", "Team Member", "Guest", "Family", "Friend"])
            relationship = st.selectbox("Relationship", ["Resident", "Family", "Friend", "Guest", "Team Member"])
        with col2:
            address = st.text_input("Address")
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

                # Upload photo to S3
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

                # Save to DynamoDB
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
                    st.success(f"✅ {name} added to registry successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save resident: {e}")
