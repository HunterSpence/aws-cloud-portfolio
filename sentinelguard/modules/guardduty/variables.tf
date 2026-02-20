variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "sentinelguard"
}

variable "publishing_frequency" {
  description = "Finding publishing frequency"
  type        = string
  default     = "FIFTEEN_MINUTES"
}

variable "enable_eks_protection" {
  description = "Enable EKS audit log monitoring"
  type        = bool
  default     = true
}

variable "sns_kms_key_id" {
  description = "KMS key ID for SNS topic encryption"
  type        = string
  default     = "alias/aws/sns"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
