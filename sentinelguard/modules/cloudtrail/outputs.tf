output "trail_arn" {
  description = "CloudTrail ARN"
  value       = aws_cloudtrail.this.arn
}

output "trail_name" {
  description = "CloudTrail name"
  value       = aws_cloudtrail.this.name
}

output "s3_bucket_id" {
  description = "S3 bucket for CloudTrail logs"
  value       = aws_s3_bucket.cloudtrail.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for CloudTrail logs"
  value       = aws_s3_bucket.cloudtrail.arn
}

output "kms_key_arn" {
  description = "KMS key ARN used for CloudTrail encryption"
  value       = aws_kms_key.cloudtrail.arn
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch Log Group ARN"
  value       = aws_cloudwatch_log_group.cloudtrail.arn
}
