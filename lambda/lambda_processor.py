import json
import boto3
import time
import re
from boto3.dynamodb.conditions import Key

rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table('ImageAnalysisResults')
registry_table = dynamodb.Table('SecureGuard_Registry')

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:378494867598:SecureGuard-Alerts"
CRITICAL_LABELS = {"Knife", "Gun", "Weapon", "Rifle", "Pistol", "Dagger", "Blade"}  # keep in sync with app/config.py DANGER_LABELS
BODY_PART_LABELS = {"Finger", "Hand", "Body Part", "Face", "Head", "Arm", "Leg", "Ear", "Eye", "Nose", "Mouth", "Neck", "Shoulder", "Thumb", "Person", "Human", "Portrait", "Selfie", "Photography"}


def get_team_members():
    response = registry_table.scan()
    return {item['ImageKey']: item['Name'] for item in response.get('Items', [])}


def sanitize_key(key):
    return re.sub(r'[^a-zA-Z0-9._\-/]', '', key)


def get_severity(threats, is_verified, identity):
    if any(t in CRITICAL_LABELS for t in threats):
        return "CRITICAL"
    if not is_verified and identity == "Unknown / Guest":
        return "MEDIUM"
    return "INFO"


def send_email_alert(severity, threats, identity, match_confidence, key, timestamp):
    emoji = "🔴" if severity == "CRITICAL" else "🟡" if severity == "MEDIUM" else "🔵"
    subject = f"{emoji} SecureGuard {severity} Alert — {', '.join(threats).upper()}"
    message = f"""
SecureGuard Security Alert
==========================
Severity:    {severity}
Timestamp:   {timestamp}
Threat:      {', '.join(threats).upper()}
Identity:    {identity}
Confidence:  {match_confidence}
Image Key:   {key}

This is an automated alert from your SecureGuard Biometric Platform.
"""
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)


def lambda_handler(event, context):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        raw_key = event['Records'][0]['s3']['object']['key']
        key = sanitize_key(raw_key)

        if not key or key != raw_key:
            print(f"Rejected suspicious key: {raw_key}")
            return {'statusCode': 400, 'body': 'Invalid key'}

        if key.endswith('.json'):
            return {'statusCode': 200, 'body': 'File skipped (System File)'}

        print(f"New Capture Detected: {key}. Starting Team Verification...")

        identity = "Unknown / Guest"
        is_verified = False
        match_confidence = "N/A"
        threats = []

        team_members = get_team_members()

        # --- FACE CHECK ---
        face_check = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, Attributes=['DEFAULT']
        )
        if not face_check['FaceDetails']:
            table.put_item(Item={
                'ImageId': key,
                'Timestamp': str(int(time.time())),
                'Identity': 'No Face Detected',
                'Status': 'GUEST_ACCESS',
                'Severity': 'INFO',
                'AlertStatus': 'New',
                'MatchConfidence': 'N/A',
                'TopEmotion': 'N/A',
                'AgeRange': 'N/A',
                'WearingHolding': [],
                'DetectedLabels': [],
                'BucketSource': bucket
            })
            return {'statusCode': 200, 'body': 'No face detected in image'}

        # --- FACE MATCHING ---
        for image_key, name in team_members.items():
            compare_res = rekognition.compare_faces(
                SourceImage={'S3Object': {'Bucket': bucket, 'Name': image_key}},
                TargetImage={'S3Object': {'Bucket': bucket, 'Name': key}},
                SimilarityThreshold=80
            )
            if compare_res['FaceMatches']:
                identity = f"{name} (Team Member)"
                is_verified = True
                match_confidence = f"{compare_res['FaceMatches'][0]['Similarity']:.1f}%"
                print(f"Match Found: {identity} ({match_confidence})")
                break

        # --- OBJECT & ATTRIBUTE ANALYTICS ---
        label_res = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, MaxLabels=15, MinConfidence=75
        )
        face_res = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, Attributes=['ALL']
        )

        all_labels = [l['Name'] for l in label_res['Labels']]
        threats = [l for l in all_labels if l in CRITICAL_LABELS]
        scene_objects = [l for l in all_labels if l not in BODY_PART_LABELS]

        emotion = "N/A"
        age_range = "N/A"
        if face_res['FaceDetails']:
            face = face_res['FaceDetails'][0]
            emotion = face['Emotions'][0]['Type'] if face['Emotions'] else 'N/A'
            age_range = f"{face['AgeRange']['Low']}-{face['AgeRange']['High']}"

        # --- SEVERITY ---
        severity = get_severity(threats, is_verified, identity)

        # --- SEND EMAIL IF CRITICAL OR MEDIUM ---
        if severity in ("CRITICAL", "MEDIUM") and threats:
            try:
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                send_email_alert(severity, threats if threats else [identity], identity, match_confidence, key, ts)
                print(f"Email alert sent: {severity}")
            except Exception as e:
                print(f"SNS error: {e}")

        # --- SAVE TO DYNAMODB ---
        table.put_item(Item={
            'ImageId': key,
            'Timestamp': str(int(time.time())),
            'Identity': identity,
            'Status': "AUTHORIZED" if is_verified else "GUEST_ACCESS",
            'Severity': severity,
            'AlertStatus': 'New',
            'MatchConfidence': match_confidence,
            'TopEmotion': emotion,
            'AgeRange': age_range,
            'WearingHolding': scene_objects[:5],
            'DetectedLabels': all_labels,
            'BucketSource': bucket
        })

        print(f"LOG SUCCESS: {identity} saved to DynamoDB.")
        return {'statusCode': 200, 'body': json.dumps(f"Result: {identity}")}

    except Exception as e:
        print(f"Pipeline Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}
