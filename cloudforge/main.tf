# =============================================================================
# CloudForge — Root Module
# =============================================================================
# Orchestrates all infrastructure modules. Each module is independently
# testable and reusable. Dependencies flow top-down:
#   VPC → ECS + Database → CDN → Monitoring
# =============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.additional_tags, {
    Project     = var.project_name
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# VPC — Foundation layer
# Multi-AZ networking with public, private, and database subnets.
# -----------------------------------------------------------------------------
module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway
  tags               = local.common_tags
}

# -----------------------------------------------------------------------------
# ECS — Compute layer
# Fargate cluster with ALB, auto-scaling, and ECR repository.
# Deployed into private subnets; ALB in public subnets.
# -----------------------------------------------------------------------------
module "ecs" {
  source = "./modules/ecs"

  project_name    = var.project_name
  environment     = var.environment
  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnet_ids
  private_subnets = module.vpc.private_subnet_ids
  container_image = var.container_image
  container_port  = var.container_port
  task_cpu        = var.ecs_task_cpu
  task_memory     = var.ecs_task_memory
  desired_count   = var.ecs_desired_count
  min_capacity    = var.ecs_min_capacity
  max_capacity    = var.ecs_max_capacity
  tags            = local.common_tags
}

# -----------------------------------------------------------------------------
# Database — Data layer
# Aurora PostgreSQL cluster with encryption, automated backups,
# and a read replica for read-heavy workloads.
# -----------------------------------------------------------------------------
module "database" {
  source = "./modules/database"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  database_subnets      = module.vpc.database_subnet_ids
  instance_class        = var.db_instance_class
  database_name         = var.db_name
  master_username       = var.db_master_username
  backup_retention_days = var.db_backup_retention_days
  deletion_protection   = var.db_deletion_protection
  allowed_security_groups = [module.ecs.service_security_group_id]
  tags                  = local.common_tags
}

# -----------------------------------------------------------------------------
# CDN — Edge layer
# CloudFront distribution with WAF, TLS via ACM, and Route 53 DNS.
# ACM certificate is provisioned in us-east-1 (CloudFront requirement).
# -----------------------------------------------------------------------------
module "cdn" {
  source = "./modules/cdn"

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }

  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.domain_name
  alb_dns_name = module.ecs.alb_dns_name
  alb_zone_id  = module.ecs.alb_zone_id
  enable_waf   = var.enable_waf
  tags         = local.common_tags
}

# -----------------------------------------------------------------------------
# Monitoring — Observability layer
# CloudWatch dashboards, alarms, SNS notifications, and log groups.
# Monitors ECS, ALB, Aurora, and NAT Gateway metrics.
# -----------------------------------------------------------------------------
module "monitoring" {
  source = "./modules/monitoring"

  project_name        = var.project_name
  environment         = var.environment
  alert_email         = var.alert_email
  log_retention_days  = var.log_retention_days
  ecs_cluster_name    = module.ecs.cluster_name
  ecs_service_name    = module.ecs.service_name
  alb_arn_suffix      = module.ecs.alb_arn_suffix
  target_group_arn_suffix = module.ecs.target_group_arn_suffix
  db_cluster_id       = module.database.cluster_identifier
  tags                = local.common_tags
}
