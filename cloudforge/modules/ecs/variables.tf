variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "private_subnet_ids" { type = list(string) }
variable "container_image" { type = string; default = "nginx:latest" }
variable "container_port" { type = number; default = 80 }
variable "desired_count" { type = number; default = 2 }
variable "cpu" { type = number; default = 256 }
variable "memory" { type = number; default = 512 }
variable "min_capacity" { type = number; default = 1 }
variable "max_capacity" { type = number; default = 10 }
variable "tags" { type = map(string); default = {} }
