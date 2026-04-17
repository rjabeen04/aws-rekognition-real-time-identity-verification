import json
import boto3
import time

rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ImageAnalysisResults')
registry_table = dynamodb.Table('SecureGuard_Registry')

def get_team_members():
    """Fetch registered members dynamically from DynamoDB."""
    response = registry_table.scan()
    return {item['ImageKey']: item['Name'] for item in response.get('Items', [])}
BODY_PART_LABELS = {"Finger", "Hand", "Body Part", "Face", "Head", "Arm", "Leg", "Ear", "Eye", "Nose", "Mouth", "Neck", "Shoulder", "Thumb", "Person", "Human", "Portrait", "Selfie", "Photography"}

def lambda_handler(event, context):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        if key.endswith('.json'):
            return {'statusCode': 200, 'body': 'File skipped (System File)'}

        print(f"New Capture Detected: {key}. Starting Team Verification...")

        # --- 1. FACE MATCHING ---
        identity = "Unknown / Guest"
        is_verified = False
        match_confidence = "N/A"

        # Fetch team members dynamically from registry
        team_members = get_team_members()

        # Check if there is a face in the captured image first
        face_check = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, Attributes=['DEFAULT']
        )
        if not face_check['FaceDetails']:
            table.put_item(Item={
                'ImageId': key,
                'Timestamp': str(int(time.time())),
                'Identity': 'No Face Detected',
                'Status': 'GUEST_ACCESS',
                'MatchConfidence': 'N/A',
                'TopEmotion': 'N/A',
                'AgeRange': 'N/A',
                'WearingHolding': [],
                'DetectedLabels': [],
                'BucketSource': bucket
            })
            return {'statusCode': 200, 'body': 'No face detected in image'}

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

        # --- 2. OBJECT & ATTRIBUTE ANALYTICS ---
        label_res = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, MaxLabels=15, MinConfidence=75
        )
        face_res = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, Attributes=['ALL']
        )

        # All labels
        all_labels = [l['Name'] for l in label_res['Labels']]

        # Filter out body parts to get wearing/holding objects
        scene_objects = [l for l in all_labels if l not in BODY_PART_LABELS]

        # Face attributes
        emotion = "N/A"
        age_range = "N/A"

        if face_res['FaceDetails']:
            face = face_res['FaceDetails'][0]
            emotion = face['Emotions'][0]['Type']
            age_range = f"{face['AgeRange']['Low']}-{face['AgeRange']['High']}"

        # --- 3. SAVE TO DYNAMODB ---
        table.put_item(
            Item={
                'ImageId': key,
                'Timestamp': str(int(time.time())),
                'Identity': identity,
                'Status': "AUTHORIZED" if is_verified else "GUEST_ACCESS",
                'MatchConfidence': match_confidence,
                'TopEmotion': emotion,
                'AgeRange': age_range,
                'WearingHolding': scene_objects[:5],
                'DetectedLabels': all_labels,
                'BucketSource': bucket
            }
        )

        print(f"LOG SUCCESS: {identity} saved to DynamoDB.")
        return {'statusCode': 200, 'body': json.dumps(f"Result: {identity}")}

    except Exception as e:
        print(f"Pipeline Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}
