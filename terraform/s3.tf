resource "aws_s3_bucket_server_side_encryption_configuration" "raw_captures_encryption" {
  bucket = aws_s3_bucket.raw_captures.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "raw_captures_versioning" {
  bucket = aws_s3_bucket.raw_captures.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "raw_captures_public_access" {
  bucket = aws_s3_bucket.raw_captures.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}
