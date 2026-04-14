# Real-Time Object and Face Recognition using AWS Rekognition
## 🛡️ SecureGuard: Cloud Biometric Identity Platform

### 🏗️ Architecture
1. **Acquisition:** OpenCV captures frames via MacBook webcam.
2. **Storage:** Images are uploaded to **Amazon S3**.
3. **Trigger:** S3 events launch an **AWS Lambda** function.
4. **AI Analysis:** **AWS Rekognition** performs face matching and emotion detection.
5. **Persistence:** Verified metadata is logged in **Amazon DynamoDB**.

### 🚀 Technical Stack
- **Language:** Python (Boto3, OpenCV, Pandas, Streamlit)
- **Cloud:** AWS (S3, Lambda, Rekognition, DynamoDB, IAM)
- **Infrastructure:** Event-Driven Serverless Architecture
