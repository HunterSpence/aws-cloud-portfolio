variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "sentinelguard"
}

variable "enable_finding_aggregator" {
  description = "Enable cross-region finding aggregation"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
