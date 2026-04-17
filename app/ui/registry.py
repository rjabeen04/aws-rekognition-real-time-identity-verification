import streamlit as st
import boto3
from PIL import Image, ImageOps
import io
from app.config import BUCKET_NAME, TEAM_MEMBERS


def render_registry(s3):
    st.markdown('<h2 style="color:white;">👥 Identity Registry</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#aaaaaa; font-size:1.1rem;">Registered users authorized for access.</p>', unsafe_allow_html=True)
    st.markdown("---")

    cols = st.columns(len(TEAM_MEMBERS))
    for idx, (filename, name) in enumerate(TEAM_MEMBERS.items()):
        with cols[idx]:
            try:
                img_obj = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
                img_bytes = img_obj['Body'].read()
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img)
                st.image(img, width=200)
            except Exception:
                st.markdown('<p style="color:#ff4444;">Image not found in S3</p>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#001a0e; border:1px solid #00ffcc; border-radius:8px; padding:12px; text-align:center; margin-top:8px;">
                <p style="color:#00ffcc; font-size:1.3rem; font-weight:900; margin:0;">{name.upper()}</p>
                <p style="color:#aaaaaa; font-size:0.95rem; margin:4px 0;">📁 {filename}</p>
                <p style="color:#00ffcc; font-size:0.95rem; font-weight:700; margin:0;">✅ ACTIVE</p>
            </div>""", unsafe_allow_html=True)
