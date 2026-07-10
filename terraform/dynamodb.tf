resource "aws_dynamodb_table" "image_analysis" {
  name         = "ImageAnalysisResults"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "ImageId"
  range_key = "Timestamp"

  attribute {
    name = "ImageId"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "S"
  }

  tags = {
    Name    = "Image Analysis Results"
    Project = "SecureGuard"
  }
}

