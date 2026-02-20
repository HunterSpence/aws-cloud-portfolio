output "guardduty_detector_id" { value = var.enable_guardduty ? aws_guardduty_detector.main[0].id : null }
output "securityhub_arn" { value = var.enable_securityhub ? aws_securityhub_account.main[0].id : null }
output "config_recorder_id" { value = var.enable_config ? aws_config_configuration_recorder.main[0].id : null }
output "sns_alert_topic_arn" { value = aws_sns_topic.security_alerts.arn }
output "cloudtrail_arn" { value = aws_cloudtrail.main.arn }
output "remediation_lambda_arn" { value = aws_lambda_function.auto_remediate.arn }
