output "securityhub_arn" {
  description = "Security Hub ARN"
  value       = aws_securityhub_account.this.arn
}

output "cis_subscription_arn" {
  description = "CIS Benchmark subscription ARN"
  value       = aws_securityhub_standards_subscription.cis.id
}

output "foundational_subscription_arn" {
  description = "AWS Foundational Best Practices subscription ARN"
  value       = aws_securityhub_standards_subscription.aws_foundational.id
}

output "event_rule_arn" {
  description = "EventBridge rule ARN for critical findings"
  value       = aws_cloudwatch_event_rule.securityhub_findings.arn
}
