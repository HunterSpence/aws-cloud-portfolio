# =============================================================================
# CloudForge — Root Outputs
# =============================================================================

# --- Networking ---
output "vpc_id" {
  description = "ID of the primary VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs across all AZs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs across all AZs"
  value       = module.vpc.private_subnet_ids
}

# --- Compute ---
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecs.ecr_repository_url
}

# --- Database ---
output "aurora_cluster_endpoint" {
  description = "Aurora cluster writer endpoint"
  value       = module.database.cluster_endpoint
}

output "aurora_reader_endpoint" {
  description = "Aurora cluster reader endpoint"
  value       = module.database.reader_endpoint
}

# --- CDN ---
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cdn.distribution_domain_name
}

output "website_url" {
  description = "Full website URL (if domain configured)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${module.cdn.distribution_domain_name}"
}

# --- Monitoring ---
output "sns_topic_arn" {
  description = "ARN of the SNS alerting topic"
  value       = module.monitoring.sns_topic_arn
}

output "dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}
