BUCKET_NAME = "rekognition-project-raw-captures"
DYNAMO_TABLE = "ImageAnalysisResults"
DATA_FILE = "session_data.json"

DANGER_LABELS = {
    "Phone", "Mobile Phone", "Cell Phone", "Weapon", "Knife",
    "Gun", "Pistol", "Rifle", "Iphone", "Smartphone",
    "Telephone", "Android Phone"
}

BODY_PART_LABELS = {
    "Finger", "Hand", "Body Part", "Face", "Head", "Arm",
    "Leg", "Ear", "Eye", "Nose", "Mouth", "Neck", "Shoulder", "Thumb"
}

TEAM_MEMBERS = {
    "reshma.jpg": "Reshma",
    "david.jpg": "David",
    "hilton.jpeg": "Hilton"
}
