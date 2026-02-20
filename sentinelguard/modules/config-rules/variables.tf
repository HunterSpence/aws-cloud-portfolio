variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
  default     = "sentinelguard"
}

variable "config_s3_bucket" {
  description = "S3 bucket name for AWS Config delivery"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
