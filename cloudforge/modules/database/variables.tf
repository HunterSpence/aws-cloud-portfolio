variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "app_security_group_ids" { type = list(string) }
variable "db_name" { type = string; default = "appdb" }
variable "db_master_username" { type = string; default = "admin" }
variable "db_instance_class" { type = string; default = "db.r6g.large" }
variable "db_backup_retention" { type = number; default = 7 }
variable "tags" { type = map(string); default = {} }
