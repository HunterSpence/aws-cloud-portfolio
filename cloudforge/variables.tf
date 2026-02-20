# =============================================================================
# CloudForge — Root Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------
variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "cloudforge"
}

variable "environment" {
  description = "Deployment environment (production, staging, development)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

# -----------------------------------------------------------------------------
# Regions
# -----------------------------------------------------------------------------
variable "primary_region" {
  description = "Primary AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "dr_region" {
  description = "Disaster recovery / secondary region"
  type        = string
  default     = "eu-west-1"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the primary VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones (3 for HA)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateways for private subnets (disable to save cost in dev)"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway instead of one per AZ (cost savings for non-prod)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# ECS / Compute
# -----------------------------------------------------------------------------
variable "container_image" {
  description = "Docker image URI for the ECS service (ECR or public)"
  type        = string
  default     = ""
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8080
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS task (256 = 0.25 vCPU)"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory (MiB) for ECS task"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks for auto-scaling"
  type        = number
  default     = 2
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks for auto-scaling"
  type        = number
  default     = 10
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
variable "db_instance_class" {
  description = "Aurora instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "db_name" {
  description = "Name of the default database"
  type        = string
  default     = "cloudforge"
}

variable "db_master_username" {
  description = "Master username for Aurora cluster"
  type        = string
  default     = "cloudforge_admin"
  sensitive   = true
}

variable "db_backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7
}

variable "db_deletion_protection" {
  description = "Enable deletion protection on the database"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# CDN / DNS
# -----------------------------------------------------------------------------
variable "domain_name" {
  description = "Root domain name (must be a Route 53 hosted zone)"
  type        = string
  default     = ""
}

variable "enable_waf" {
  description = "Enable AWS WAF on CloudFront distribution"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------
variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log group retention in days"
  type        = number
  default     = 30
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
