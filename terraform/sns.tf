resource "aws_sns_topic" "secureguard_alerts" {
  name = "secureguard-alerts"

  tags = {
    Name    = "SecureGuard Alerts"
    Project = "SecureGuard"
  }
}
