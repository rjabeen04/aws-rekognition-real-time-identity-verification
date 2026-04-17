import cv2
import boto3
import datetime
import time

# 1. Initialize AWS clients
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

# --- CONFIGURATION ---
BUCKET_NAME = 'rekognition-project-raw-captures' 
# Match this to your Lambda Team Registry
TEAM_MEMBERS = ["reshma.jpg", "selina.jpg","david.jpg","hilton.jpg"] 

def capture_and_analyze():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print(f"Webcam started. Press 's' to analyze, or 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        cv2.imshow("Real-Time Object and Face Recognition", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"capture_{timestamp}.jpg"
            
            cv2.imwrite(file_name, frame)
            print(f"\n[1] Saved locally as {file_name}")

            try:
                # 2. Upload to S3 (This triggers the Lambda!)
                print(f"[2] Uploading to S3...")
                s3.upload_file(file_name, BUCKET_NAME, file_name)
                time.sleep(1) 

                # 3. Analyze Objects
                print("[3] Analyzing Objects...")
                label_response = rekognition.detect_labels(
                    Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}},
                    MaxLabels=5
                )
                
                is_human = any(l['Name'] in ['Person', 'Human', 'Face'] for l in label_response['Labels'])

                # 4. Analyze Identity (Looping through the Team Registry)
                identity = "Unknown / Guest"
                if is_human:
                    print(f"[4] Checking Team Registry...")
                    for member_file in TEAM_MEMBERS:
                        id_response = rekognition.compare_faces(
                            SourceImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': member_file}},
                            TargetImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}},
                            SimilarityThreshold=80
                        )
                        
                        if id_response['FaceMatches']:
                            name = member_file.split('.')[0].capitalize()
                            identity = f"{name} (Verified)"
                            break 
                else:
                    identity = "Non-Human Object"

                # 5. Analyze Face Details
                face_response = rekognition.detect_faces(
                    Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}},
                    Attributes=['ALL']
                )
                
                if face_response['FaceDetails']:
                    print("\n--- Face Details ---")
                    img_h, img_w, _ = frame.shape
                    face = face_response['FaceDetails'][0]
                    
                    age_low = face['AgeRange']['Low']
                    age_high = face['AgeRange']['High']
                    emotion = face['Emotions'][0]['Type']
                    
                    print(f"Identity: {identity}")
                    print(f"Age Range: {age_low} - {age_high}")
                    print(f"Top Emotion: {emotion}")

                    # UI Feedback on the frame
                    box = face['BoundingBox']
                    cv2.rectangle(frame, 
                                  (int(box['Left'] * img_w), int(box['Top'] * img_h)), 
                                  (int((box['Left'] + box['Width']) * img_w), int((box['Top'] + box['Height']) * img_h)), 
                                  (0, 255, 0), 3)
                    
                    cv2.putText(frame, f"{identity} | {emotion}", 
                                (int(box['Left'] * img_w), int(box['Top'] * img_h) - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    cv2.imshow("Analysis Result", frame)
                    cv2.waitKey(3000) 
                    cv2.destroyWindow("Analysis Result")
                
                print(f"FINAL RESULT: {identity}")

            except Exception as e:
                print(f"Error: {e}")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_analyze()