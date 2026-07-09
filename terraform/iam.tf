
resource "aws_iam_role" "lambda_execution_role" {
  name = "secureguard-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "lambda.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name    = "SecureGuard Lambda Execution Role"
    Project = "SecureGuard"
  }
}



