resource "aws_rekognition_collection" "face_collection" {
  collection_id = "secureguard-face-collection"

  tags = {
    Name    = "SecureGuard Face Collection"
    Project = "SecureGuard"
  }
}
