# =============================================================================
# CloudForge — Remote State Backend
# =============================================================================
# S3 bucket for state storage with DynamoDB table for state locking.
# Prerequisites (create once via bootstrap or CLI):
#   aws s3api create-bucket --bucket cloudforge-tfstate-<ACCOUNT_ID> --region us-east-1
#   aws dynamodb create-table --table-name cloudforge-tfstate-lock \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST --region us-east-1
# =============================================================================

terraform {
  backend "s3" {
    bucket         = "cloudforge-tfstate"
    key            = "cloudforge/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "cloudforge-tfstate-lock"

    # Recommended: enable versioning on the S3 bucket for state recovery
    # aws s3api put-bucket-versioning --bucket cloudforge-tfstate \
    #   --versioning-configuration Status=Enabled
  }
}
