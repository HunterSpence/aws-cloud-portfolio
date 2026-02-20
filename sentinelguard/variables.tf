variable "project_name" { type = string; default = "sentinelguard" }
variable "environment" { type = string; default = "production" }
variable "aws_region" { type = string; default = "us-east-1" }
variable "alert_email" { type = string; description = "Email for security alerts" }
variable "slack_webhook_url" { type = string; default = ""; description = "Slack webhook for alerts" }
variable "enable_guardduty" { type = bool; default = true }
variable "enable_securityhub" { type = bool; default = true }
variable "enable_config" { type = bool; default = true }
variable "enable_auto_remediation" { type = bool; default = false; description = "Auto-remediate findings (use with caution)" }
variable "severity_threshold" { type = string; default = "MEDIUM"; description = "Minimum severity for alerts: LOW, MEDIUM, HIGH, CRITICAL" }
variable "tags" { type = map(string); default = { Project = "SentinelGuard", ManagedBy = "Terraform" } }
