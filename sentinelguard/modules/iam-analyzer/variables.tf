variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "sentinelguard"
}

variable "enable_org_analyzer" {
  description = "Enable organization-level analyzer"
  type        = bool
  default     = false
}

variable "trusted_account_ids" {
  description = "List of trusted AWS account IDs to auto-archive"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
