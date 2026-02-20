variable "project_name" {
  type        = string
  description = "Project name for resource tagging"
}

variable "environment" {
  type        = string
  description = "Environment (dev/staging/production)"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags for resources"
}
