# 🛡️ SecureGuard: Cloud Biometric Identity Platform

A real-time face recognition and threat detection system built on AWS serverless architecture. Captures webcam images via a Streamlit dashboard, processes them through an event-driven AWS pipeline, and displays live identity verification and security alerts.

---

## 🏗️ Architecture

```
Browser Webcam (Streamlit)
        ↓
   Amazon S3
   (rekognition-project-raw-captures)
        ↓
   S3 Event Notification
        ↓
   AWS Lambda
   (image-processor)
        ↓
   AWS Rekognition
   ├── compare_faces     → Identity matching against registry
   ├── detect_labels     → Threat detection (phone, weapon, etc.)
   └── detect_faces      → Emotion + Age analysis
        ↓
   Amazon DynamoDB
   (ImageAnalysisResults)
        ↓
   Streamlit polls DynamoDB
        ↓
   Live Dashboard (Results displayed)
```

---

## ✅ Features

- **Real-time face matching** — compares webcam capture against registered identity photos in S3
- **Threat detection** — detects phones, weapons, and other dangerous objects instantly
- **Unknown person detection** — denies access if face doesn't match any registered user
- **Emotion & age analysis** — displays real Rekognition face attribute results
- **Live dashboard** — stats, alerts, and access logs update after every scan
- **Session persistence** — data survives page refreshes via local JSON + DynamoDB
- **CSV export** — download alerts and access logs as CSV
- **Pulsing red alert** — animated threat card for visual security alerts

---

## 🚀 Technical Stack

| Layer | Technology |
|---|---|
| Frontend | Python, Streamlit |
| Cloud Storage | Amazon S3 |
| Serverless Compute | AWS Lambda |
| AI / Vision | AWS Rekognition |
| Database | Amazon DynamoDB |
| SDK | Boto3 |
| Infrastructure | Event-Driven Serverless |

---

## 📁 Project Structure

```
├── main.py                  # Entry point — Streamlit dashboard
├── app/
│   ├── config.py            # Constants & danger labels
│   ├── aws_clients.py       # boto3 client initialization
│   ├── rekognition.py       # DynamoDB polling & data persistence
│   └── ui/
│       ├── dashboard.py     # Main scanner & identity verification
│       ├── alerts.py        # Security alerts tab
│       ├── logs.py          # Access history tab
│       ├── registry.py      # Registered users tab
│       ├── settings.py      # Configurable settings tab
│       └── styles.py        # CSS styles
├── lambda/
│   └── lambda_processor.py  # AWS Lambda function
├── app.py                   # Original OpenCV terminal app
├── Dockerfile               # Container for team deployment
├── requirements.txt
└── README.md
```

---

## ⚙️ AWS Services Setup

### S3 Bucket
- Bucket: `rekognition-project-raw-captures`
- Reference images stored: `reshma.jpg`, `david.jpg`, `hilton.jpeg`
- S3 Event Notification configured to trigger Lambda on `s3:ObjectCreated:*`

### Lambda Function
- Function: `image-processor`
- Runtime: Python 3.14
- Handler: `lambda_processor.lambda_handler`
- Timeout: 30 seconds
- Trigger: S3 Event Notification
- Permissions: S3 read, Rekognition full access, DynamoDB write

### DynamoDB Table
- Table: `ImageAnalysisResults`
- Partition key: `ImageId` (String)
- Sort key: `Timestamp` (String)
- Stores: Identity, Status, TopEmotion, AgeRange, DetectedLabels

### Rekognition
- `compare_faces` — 80% similarity threshold for identity matching
- `detect_labels` — threat object detection
- `detect_faces` — emotion and age range analysis

---

## 🖥️ Local Setup

**1. Create conda environment:**
```bash
conda create -n secureguard python=3.10 -y
conda activate secureguard
```

**2. Install dependencies:**
```bash
pip install streamlit boto3 opencv-python-headless Pillow pandas
```

**3. Configure AWS credentials:**
```bash
aws configure
```

**4. Run the dashboard:**
```bash
streamlit run main.py
```

---

## 🔒 Security Outcomes

| Scenario | Result |
|---|---|
| Registered face (Reshma, David, Hilton) | ✅ IDENTITY VERIFIED — Access Granted |
| Unregistered / unknown face | 🚫 UNKNOWN PERSON — Access Denied |
| Phone / weapon detected | 🚨 SECURITY ALERT — Access Denied |
| No face in frame | 🔍 No person detected — prompts repositioning |

---

## 🔐 IAM Security — Principle of Least Privilege

Each AWS service is granted **only the minimum permissions required** — no wildcard `*` policies.

### Lambda Execution Role (`image-processor-role`)

| Permission | Resource | Reason |
|---|---|---|
| `s3:GetObject` | `arn:aws:s3:::rekognition-project-raw-captures/*` | Read captures + reference images |
| `rekognition:CompareFaces` | `*` | Face matching |
| `rekognition:DetectLabels` | `*` | Object/threat detection |
| `rekognition:DetectFaces` | `*` | Emotion + age analysis |
| `dynamodb:PutItem` | `arn:aws:dynamodb:us-east-1:*:table/ImageAnalysisResults` | Write results only |
| `logs:CreateLogGroup` | `arn:aws:logs:*` | CloudWatch logging |

### Streamlit App IAM User

| Permission | Resource | Reason |
|---|---|---|
| `s3:PutObject` | `arn:aws:s3:::rekognition-project-raw-captures/*` | Upload captures |
| `s3:GetObject` | `arn:aws:s3:::rekognition-project-raw-captures/*` | Load registry photos |
| `rekognition:DetectLabels` | `*` | Local threat detection |
| `dynamodb:Query` | `arn:aws:dynamodb:us-east-1:*:table/ImageAnalysisResults` | Poll results |

> No `AdministratorAccess` or `FullAccess` policies used anywhere in this project.

---

## 👤 Registered Users

| Name | Reference Image |
|---|---|
| Reshma | `reshma.jpg` |
| David | `david.jpg` |
| Hilton | `hilton.jpeg` |
