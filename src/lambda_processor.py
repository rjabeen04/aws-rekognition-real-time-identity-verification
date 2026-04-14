import json
import boto3
import time

# Initialize AWS clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ImageAnalysisResults')

# --- 1. THE TEAM REGISTRY ---
# Add your teammates' filenames exactly as they appear in S3
TEAM_MEMBERS = ["reshma.jpg", "hilton.jpg", "david.jpg", "selina.jpg"]

def lambda_handler(event, context):
    try:
        # Get bucket and file name from the S3 Event notification
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # Security Filter: Ignore the reference photos and metadata files
        if key in TEAM_MEMBERS or key.endswith('.json'):
            return {'statusCode': 200, 'body': 'File skipped (System File)'}
            
        print(f"New Capture Detected: {key}. Starting Team Verification...")

        # --- 2. MULTI-USER IDENTITY LOOP ---
        identity = "Unknown / Guest" # Default if no match is found
        is_verified = False
        
        for member_file in TEAM_MEMBERS:
            print(f"Comparing against {member_file}...")
            
            # 1:1 Comparison check
            compare_res = rekognition.compare_faces(
                SourceImage={'S3Object': {'Bucket': bucket, 'Name': member_file}},
                TargetImage={'S3Object': {'Bucket': bucket, 'Name': key}},
                SimilarityThreshold=80
            )

            if compare_res['FaceMatches']:
                # Extract the name (e.g., "reshma.jpg" -> "Reshma")
                name = member_file.split('.')[0].capitalize()
                identity = f"{name} (Team Member)"
                is_verified = True
                print(f"Match Found: {identity}")
                break  # Exit loop early once we find the right person

        # --- 3. OBJECT & ATTRIBUTE ANALYTICS ---
        label_res = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, MaxLabels=5
        )
        face_res = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}}, Attributes=['ALL']
        )

        # Process labels, emotions, and age
        labels = [l['Name'] for l in label_res['Labels']]
        emotion = "N/A"
        age_range = "N/A"
        
        if face_res['FaceDetails']:
            emotion = face_res['FaceDetails'][0]['Emotions'][0]['Type']
            low = face_res['FaceDetails'][0]['AgeRange']['Low']
            high = face_res['FaceDetails'][0]['AgeRange']['High']
            age_range = f"{low}-{high}"

        # --- 4. SAVE TO DYNAMODB (The Audit Trail) ---
        table.put_item(
            Item={
                'ImageId': key,
                'Timestamp': str(int(time.time())),
                'Identity': identity,
                'Status': "AUTHORIZED" if is_verified else "GUEST_ACCESS",
                'TopEmotion': emotion,
                'AgeRange': age_range,
                'DetectedLabels': labels,
                'BucketSource': bucket
            }
        )

        print(f"LOG SUCCESS: {identity} record saved to DynamoDB.")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Result: {identity}")
        }

    except Exception as e:
        print(f"Pipeline Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}