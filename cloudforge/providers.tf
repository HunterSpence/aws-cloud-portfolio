# =============================================================================
# CloudForge — Provider Configuration
# =============================================================================
# Multi-region AWS setup with primary and disaster recovery providers.
# The "dr" alias enables cross-region resources (e.g., CloudFront certs
# must be in us-east-1, Aurora read replicas in secondary region).
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }

  # Remote state — uncomment and configure for team usage
  # backend "s3" {
  #   bucket         = "cloudforge-tfstate"
  #   key            = "infrastructure/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "cloudforge-tfstate-lock"
  #   encrypt        = true
  # }
}

# -----------------------------------------------------------------------------
# Primary Region Provider
# -----------------------------------------------------------------------------
provider "aws" {
  region = var.primary_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "cloudforge"
    }
  }
}

# -----------------------------------------------------------------------------
# DR / Secondary Region Provider
# Also used for ACM certificates (CloudFront requires us-east-1 certs)
# -----------------------------------------------------------------------------
provider "aws" {
  alias  = "dr"
  region = var.dr_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "cloudforge"
    }
  }
}

# -----------------------------------------------------------------------------
# US-East-1 provider (required for CloudFront ACM certificates)
# -----------------------------------------------------------------------------
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "cloudforge"
    }
  }
}
