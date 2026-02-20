# =============================================================================
# CloudForge — Security Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID to create security groups in"
  type        = string
}

variable "container_port" {
  description = "Port the application container listens on"
  type        = number
  default     = 8080
}

variable "kms_deletion_window" {
  description = "KMS key deletion waiting period in days"
  type        = number
  default     = 14
}

variable "db_master_password" {
  description = "Master password for Aurora PostgreSQL (stored in SSM)"
  type        = string
  sensitive   = true
  default     = "CHANGE_ME"
}

variable "app_secrets" {
  description = "Map of application secret names to values (stored in SSM as SecureString)"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
