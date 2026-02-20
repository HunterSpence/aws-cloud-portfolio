# =============================================================================
# CloudForge — Security Module Outputs
# =============================================================================

# KMS
output "kms_key_arn" {
  description = "ARN of the primary KMS encryption key"
  value       = aws_kms_key.main.arn
}

output "kms_key_id" {
  description = "ID of the primary KMS encryption key"
  value       = aws_kms_key.main.key_id
}

output "kms_alias_arn" {
  description = "ARN of the KMS key alias"
  value       = aws_kms_alias.main.arn
}

# Security Groups
output "alb_security_group_id" {
  description = "Security group ID for the ALB"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "Security group ID for application (ECS) tasks"
  value       = aws_security_group.app.id
}

output "database_security_group_id" {
  description = "Security group ID for the database tier"
  value       = aws_security_group.database.id
}

# SSM
output "db_password_ssm_arn" {
  description = "ARN of the SSM parameter storing the database password"
  value       = aws_ssm_parameter.db_password.arn
}

output "app_secret_arns" {
  description = "Map of application secret names to their SSM parameter ARNs"
  value       = { for k, v in aws_ssm_parameter.app_secrets : k => v.arn }
}
