output "detector_id" {
  description = "GuardDuty detector ID"
  value       = aws_guardduty_detector.this.id
}

output "detector_arn" {
  description = "GuardDuty detector ARN"
  value       = aws_guardduty_detector.this.arn
}

output "sns_topic_arn" {
  description = "SNS topic ARN for GuardDuty alerts"
  value       = aws_sns_topic.guardduty_alerts.arn
}
