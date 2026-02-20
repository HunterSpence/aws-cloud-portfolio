output "analyzer_arn" {
  description = "IAM Access Analyzer ARN"
  value       = aws_accessanalyzer_analyzer.account.arn
}

output "analyzer_name" {
  description = "IAM Access Analyzer name"
  value       = aws_accessanalyzer_analyzer.account.analyzer_name
}

output "event_rule_arn" {
  description = "EventBridge rule ARN for analyzer findings"
  value       = aws_cloudwatch_event_rule.access_analyzer.arn
}
