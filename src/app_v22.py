import cv2
import boto3
import datetime
import time

#Team Registry & Object-Aware Logic
# 1. Initialize AWS clients
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

# --- CONFIGURATION ---
CAPTURE_BUCKET = 'rekognition-project-raw-captures' 
REGISTRY_BUCKET = 'rekognition-project-raw-captures' # Change this if you make a separate bucket!

# The list of team members in your registry
TEAM_MEMBERS = ['reshma.jpg', 'selina.jpg'] 

def capture_and_analyze():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print(f"Webcam started. Press 's' to analyze, or 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Group Project: AWS Cloud Vision (v2 Team Mode)", frame)

        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"capture_{timestamp}.jpg"
            
            cv2.imwrite(file_name, frame)
            print(f"\n[1] Saved locally as {file_name}")

            try:
                # 2. Upload to S3
                print(f"[2] Uploading to S3...")
                s3.upload_file(file_name, CAPTURE_BUCKET, file_name)
                time.sleep(1) 

                # 3. Analyze Objects (The "Apple" Test)
                print("[3] Analyzing Objects...")
                label_response = rekognition.detect_labels(
                    Image={'S3Object': {'Bucket': CAPTURE_BUCKET, 'Name': file_name}},
                    MaxLabels=5
                )
                
                print("\n--- Objects Found ---")
                is_human = False
                for label in label_response['Labels']:
                    print(f"{label['Name']}: {label['Confidence']:.2f}%")
                    # Check if the AI sees a person or face
                    if label['Name'] in ['Person', 'Human', 'Face']:
                        is_human = True

                # 4. Analyze Identity (Only if it's a Human!)
                identity = "Unknown Person"
                if is_human:
                    print("\n[4] Human Detected. Scanning Team Database...")
                    for member_file in TEAM_MEMBERS:
                        try:
                            id_response = rekognition.compare_faces(
                                SourceImage={'S3Object': {'Bucket': REGISTRY_BUCKET, 'Name': member_file}},
                                TargetImage={'S3Object': {'Bucket': CAPTURE_BUCKET, 'Name': file_name}},
                                SimilarityThreshold=80
                            )
                            
                            if id_response['FaceMatches']:
                                name = member_file.split('.')[0].capitalize()
                                identity = f"{name} (Verified)"
                                print(f"Match found: {identity}")
                                break 
                        except Exception as e:
                            print(f"Warning: Could not compare against {member_file}.")
                else:
                    print("\n[4] No Human detected. Skipping Identity Search.")
                    identity = "Non-Human Object"

                # 5. Analyze Face Details
                face_response = rekognition.detect_faces(
                    Image={'S3Object': {'Bucket': CAPTURE_BUCKET, 'Name': file_name}},
                    Attributes=['ALL']
                )
                
                if face_response['FaceDetails']:
                    print("\n--- Face Details ---")
                    img_h, img_w, _ = frame.shape
                    
                    for face in face_response['FaceDetails']:
                        age_low = face['AgeRange']['Low']
                        age_high = face['AgeRange']['High']
                        emotion = face['Emotions'][0]['Type']
                        
                        print(f"Identity: {identity}")
                        print(f"Age Range: {age_low} - {age_high}")
                        print(f"Top Emotion: {emotion}")

                        # Drawing result
                        box = face['BoundingBox']
                        left, top = int(box['Left'] * img_w), int(box['Top'] * img_h)
                        width, height = int(box['Width'] * img_w), int(box['Height'] * img_h)

                        cv2.rectangle(frame, (left, top), (left + width, top + height), (0, 255, 0), 3)
                        label_text = f"{identity} | {emotion}"
                        cv2.putText(frame, label_text, (left, top - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    cv2.imshow("Analysis Result", frame)
                    cv2.waitKey(3000)
                    cv2.destroyWindow("Analysis Result")
                else:
                    # If it's an apple, it will land here
                    print("No facial features detected for detailed analysis.")

            except Exception as e:
                print(f"Error: {e}")
            
            print("\nReady for next capture.")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_analyze()