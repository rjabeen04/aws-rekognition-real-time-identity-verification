resource "aws_s3_bucket" "raw_captures" {
  bucket = var.bucket_name

  tags = {
    Name    = "SecureGuard Raw Captures"
    Project = "SecureGuard"
  }
}
