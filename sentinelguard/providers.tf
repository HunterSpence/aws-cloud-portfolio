terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "sentinelguard-tfstate"
    key            = "sentinelguard/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sentinelguard-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SentinelGuard"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}
