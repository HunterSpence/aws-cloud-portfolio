variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "sentinelguard"
}

variable "log_retention_days" {
  description = "Days to retain CloudTrail logs in S3 before expiration"
  type        = number
  default     = 365
}

variable "cloudwatch_log_retention" {
  description = "Days to retain CloudWatch logs"
  type        = number
  default     = 90
}

variable "force_destroy" {
  description = "Allow destroying the S3 bucket even with objects"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
