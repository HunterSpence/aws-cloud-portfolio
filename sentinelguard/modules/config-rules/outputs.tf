output "config_recorder_id" {
  description = "The ID of the AWS Config recorder"
  value       = aws_config_configuration_recorder.this.id
}

output "config_rule_arns" {
  description = "ARNs of all Config rules"
  value = {
    s3_public_read       = aws_config_config_rule.s3_bucket_public_read_prohibited.arn
    s3_public_write      = aws_config_config_rule.s3_bucket_public_write_prohibited.arn
    root_mfa             = aws_config_config_rule.root_account_mfa_enabled.arn
    cloudtrail           = aws_config_config_rule.cloudtrail_enabled.arn
    encrypted_volumes    = aws_config_config_rule.encrypted_volumes.arn
    vpc_flow_logs        = aws_config_config_rule.vpc_flow_logs_enabled.arn
    iam_password_policy  = aws_config_config_rule.iam_password_policy.arn
    rds_storage          = aws_config_config_rule.rds_storage_encrypted.arn
    restricted_ssh       = aws_config_config_rule.restricted_ssh.arn
    multi_region_trail   = aws_config_config_rule.multi_region_cloudtrail.arn
  }
}

output "config_role_arn" {
  description = "IAM role ARN used by AWS Config"
  value       = aws_iam_role.config.arn
}
