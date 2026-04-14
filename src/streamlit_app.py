import streamlit as st
import boto3
import time
import io
from PIL import Image

# 1. Initialize AWS clients
# Note: Ensure your AWS credentials are set up in ~/.aws/credentials
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

# --- CONFIGURATION ---
BUCKET_NAME = 'rekognition-project-raw-captures' 

st.set_page_config(page_title="AWS Vision Dashboard", page_icon="🛡️")

st.title("🛡️ SecureGuard: Cloud Biometric System")
st.markdown("---")

# Streamlit Camera Input
img_file = st.camera_input("Position yourself for cloud verification")

if img_file:
    # Convert the file to bytes for AWS Rekognition
    img_bytes = img_file.getvalue()
    
    # NEW: Generate a unique filename for S3 archiving
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    s3_file_name = f"gui_capture_{timestamp}.jpg"
    
    with st.spinner('☁️ Analyzing through AWS Rekognition...'):
        try:
            # 1. ARCHIVE TO S3: Save the photo before analysis
            s3.upload_fileobj(io.BytesIO(img_bytes), BUCKET_NAME, s3_file_name)

            # 2. Object Detection (The Apple/Person Check)
            label_res = rekognition.detect_labels(
                Image={'Bytes': img_bytes},
                MaxLabels=5
            )
            
            # Check if human is present
            is_human = any(label['Name'] in ['Person', 'Human', 'Face'] for label in label_res['Labels'])
            
            # 3. Identity Comparison (The "Reshma" Check)
            identity = "Unknown Person"
            if is_human:
                id_res = rekognition.compare_faces(
                    SourceImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': 'reshma.jpg'}},
                    TargetImage={'Bytes': img_bytes},
                    SimilarityThreshold=80
                )
                if id_res['FaceMatches']:
                    identity = "Reshma (Verified)"
            else:
                identity = "Non-Human Object"

            # --- UI FEEDBACK ---
            if "Verified" in identity:
                st.success(f"### ✅ Access Granted: {identity}")
            elif is_human:
                st.error("### ❌ Access Denied: Unauthorized Personnel")
            else:
                st.info(f"### 🍎 Object Detected: {label_res['Labels'][0]['Name']}")

            # Metrics Columns
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Cloud Labels")
                for label in label_res['Labels']:
                    st.write(f"🔹 {label['Name']}: {label['Confidence']:.1f}%")
            
            with col2:
                st.subheader("System Metadata")
                st.write(f"**S3 Storage Path:** `{s3_file_name}`")
                st.write(f"**Archive Bucket:** `{BUCKET_NAME}`")
                st.write(f"**Verification Target:** `reshma.jpg`")

        except Exception as e:
            st.error(f"AWS Error: {e}")

st.markdown("---")
st.caption("DevOps Infrastructure | Event-Driven Architecture")