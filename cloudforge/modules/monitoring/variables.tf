variable "project_name" { type = string }
variable "environment" { type = string }
variable "alert_email" { type = string }
variable "ecs_cluster_name" { type = string }
variable "ecs_service_name" { type = string }
variable "alb_arn_suffix" { type = string }
variable "db_cluster_id" { type = string }
variable "tags" { type = map(string); default = {} }
