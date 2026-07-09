
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



resource "aws_iam_policy" "lambda_policy" {
  name        = "secureguard-lambda-policy"
  description = "Least privilege policy for SecureGuard Lambda"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [

      {
        Sid    = "S3ReadAccess"
        Effect = "Allow"

        Action = [
          "s3:GetObject"
        ]

        Resource = [
          "${aws_s3_bucket.raw_captures.arn}/*"
        ]
      },

      {
        Sid    = "RekognitionAccess"
        Effect = "Allow"

        Action = [
          "rekognition:SearchFacesByImage",
          "rekognition:DetectFaces",
          "rekognition:DetectLabels"
        ]

        Resource = "*"
      },

      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"

        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]

        Resource = "*"
      }
    ]
  })

  tags = {
    Name    = "SecureGuard Lambda Policy"
    Project = "SecureGuard"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}





