variable "aws_region" {
  description = "AWS region where SecureGuard will be deployed"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name for raw image uploads"
  type        = string
}
