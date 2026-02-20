###############################################################################
# SentinelGuard — AWS Security & Compliance Baseline
# Root Terraform Configuration
###############################################################################

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    bucket         = "sentinelguard-tfstate"
    key            = "security/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sentinelguard-tflock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SentinelGuard"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "SecurityTeam"
    }
  }
}

###############################################################################
# Data Sources
###############################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

###############################################################################
# KMS Key — Shared encryption key for security services
###############################################################################

resource "aws_kms_key" "security" {
  description             = "SentinelGuard encryption key for security services"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowKeyAdministration"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowCloudTrailEncrypt"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${data.aws_region.current.name}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "AllowSNSEncrypt"
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey*",
          "kms:Decrypt"
        ]
        Resource = "*"
      }
    ]
  })

  tags = { Name = "${var.project_name}-security-key" }
}

resource "aws_kms_alias" "security" {
  name          = "alias/${var.project_name}-security"
  target_key_id = aws_kms_key.security.key_id
}

###############################################################################
# SNS Topic — Security notifications
###############################################################################

resource "aws_sns_topic" "security_alerts" {
  name              = "${var.project_name}-security-alerts"
  kms_master_key_id = aws_kms_key.security.id
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_sns_topic_policy" "security_alerts" {
  arn = aws_sns_topic.security_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSecurityServices"
        Effect = "Allow"
        Principal = {
          Service = [
            "events.amazonaws.com",
            "cloudwatch.amazonaws.com",
            "config.amazonaws.com"
          ]
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.security_alerts.arn
      }
    ]
  })
}

###############################################################################
# Modules
###############################################################################

module "cloudtrail" {
  source = "./modules/cloudtrail"

  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = aws_kms_key.security.arn
  account_id   = data.aws_caller_identity.current.account_id
}

module "config_rules" {
  source = "./modules/config-rules"

  project_name   = var.project_name
  environment    = var.environment
  sns_topic_arn  = aws_sns_topic.security_alerts.arn
  account_id     = data.aws_caller_identity.current.account_id

  depends_on = [module.cloudtrail]
}

module "guardduty" {
  source = "./modules/guardduty"

  project_name  = var.project_name
  environment   = var.environment
  enable        = var.enable_guardduty
  sns_topic_arn = aws_sns_topic.security_alerts.arn
}

module "securityhub" {
  source = "./modules/securityhub"

  project_name = var.project_name
  environment  = var.environment

  depends_on = [module.config_rules, module.guardduty]
}

module "iam_analyzer" {
  source = "./modules/iam-analyzer"

  project_name  = var.project_name
  environment   = var.environment
  sns_topic_arn = aws_sns_topic.security_alerts.arn
}

###############################################################################
# Lambda — Auto-Remediation
###############################################################################

data "archive_file" "auto_remediate" {
  type        = "zip"
  source_file = "${path.module}/lambdas/auto-remediate/handler.py"
  output_path = "${path.module}/.build/auto-remediate.zip"
}

resource "aws_lambda_function" "auto_remediate" {
  function_name    = "${var.project_name}-auto-remediate"
  filename         = data.archive_file.auto_remediate.output_path
  source_code_hash = data.archive_file.auto_remediate.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 256

  role = aws_iam_role.remediation_lambda.arn

  environment {
    variables = {
      SNS_TOPIC_ARN     = aws_sns_topic.security_alerts.arn
      ENVIRONMENT        = var.environment
      DRY_RUN           = var.remediation_dry_run ? "true" : "false"
      QUARANTINE_SG_TAG = "SentinelGuard-Quarantine"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = { Name = "${var.project_name}-auto-remediate" }
}

###############################################################################
# Lambda — Alert Forwarder
###############################################################################

data "archive_file" "alert_forwarder" {
  type        = "zip"
  source_file = "${path.module}/lambdas/alert-forwarder/handler.py"
  output_path = "${path.module}/.build/alert-forwarder.zip"
}

resource "aws_lambda_function" "alert_forwarder" {
  function_name    = "${var.project_name}-alert-forwarder"
  filename         = data.archive_file.alert_forwarder.output_path
  source_code_hash = data.archive_file.alert_forwarder.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 128

  role = aws_iam_role.alert_lambda.arn

  environment {
    variables = {
      SLACK_WEBHOOK_URL  = var.slack_webhook_url
      SNS_TOPIC_ARN      = aws_sns_topic.security_alerts.arn
      ENVIRONMENT        = var.environment
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = { Name = "${var.project_name}-alert-forwarder" }
}

###############################################################################
# Lambda — Compliance Reporter
###############################################################################

data "archive_file" "compliance_reporter" {
  type        = "zip"
  source_file = "${path.module}/lambdas/compliance-reporter/handler.py"
  output_path = "${path.module}/.build/compliance-reporter.zip"
}

resource "aws_lambda_function" "compliance_reporter" {
  function_name    = "${var.project_name}-compliance-reporter"
  filename         = data.archive_file.compliance_reporter.output_path
  source_code_hash = data.archive_file.compliance_reporter.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 512

  role = aws_iam_role.reporter_lambda.arn

  environment {
    variables = {
      REPORT_BUCKET  = aws_s3_bucket.reports.id
      SNS_TOPIC_ARN  = aws_sns_topic.security_alerts.arn
      ENVIRONMENT    = var.environment
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = { Name = "${var.project_name}-compliance-reporter" }
}

###############################################################################
# S3 Bucket — Compliance Reports
###############################################################################

resource "aws_s3_bucket" "reports" {
  bucket        = "${var.project_name}-compliance-reports-${data.aws_caller_identity.current.account_id}"
  force_destroy = false

  tags = { Name = "${var.project_name}-compliance-reports" }
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.security.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket                  = aws_s3_bucket.reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id
  rule {
    id     = "archive-old-reports"
    status = "Enabled"
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    expiration {
      days = 365
    }
  }
}

###############################################################################
# EventBridge Rules — Trigger Lambdas on Security Findings
###############################################################################

resource "aws_cloudwatch_event_rule" "security_findings" {
  name        = "${var.project_name}-security-findings"
  description = "Route Security Hub findings to remediation and alerting"

  event_pattern = jsonencode({
    source      = ["aws.securityhub"]
    detail-type = ["Security Hub Findings - Imported"]
    detail = {
      findings = {
        Severity = {
          Label = ["CRITICAL", "HIGH"]
        }
        Workflow = {
          Status = ["NEW"]
        }
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "remediate" {
  rule      = aws_cloudwatch_event_rule.security_findings.name
  target_id = "auto-remediate"
  arn       = aws_lambda_function.auto_remediate.arn
}

resource "aws_cloudwatch_event_target" "alert" {
  rule      = aws_cloudwatch_event_rule.security_findings.name
  target_id = "alert-forwarder"
  arn       = aws_lambda_function.alert_forwarder.arn
}

resource "aws_lambda_permission" "eventbridge_remediate" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_remediate.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.security_findings.arn
}

resource "aws_lambda_permission" "eventbridge_alert" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alert_forwarder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.security_findings.arn
}

# Scheduled compliance report — weekly
resource "aws_cloudwatch_event_rule" "weekly_report" {
  name                = "${var.project_name}-weekly-compliance-report"
  description         = "Generate weekly compliance report"
  schedule_expression = "cron(0 8 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "reporter" {
  rule      = aws_cloudwatch_event_rule.weekly_report.name
  target_id = "compliance-reporter"
  arn       = aws_lambda_function.compliance_reporter.arn
}

resource "aws_lambda_permission" "eventbridge_reporter" {
  statement_id  = "AllowEventBridgeSchedule"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.compliance_reporter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_report.arn
}

###############################################################################
# IAM Roles — Lambda Execution
###############################################################################

# --- Auto-Remediation Lambda Role ---
resource "aws_iam_role" "remediation_lambda" {
  name = "${var.project_name}-remediation-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "remediation_lambda" {
  name = "${var.project_name}-remediation-policy"
  role = aws_iam_role.remediation_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Remediation"
        Effect = "Allow"
        Action = [
          "s3:PutBucketPublicAccessBlock",
          "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketPolicyStatus"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMRemediation"
        Effect = "Allow"
        Action = [
          "iam:UpdateAccessKey",
          "iam:ListAccessKeys",
          "iam:GetAccessKeyLastUsed"
        ]
        Resource = "*"
      },
      {
        Sid    = "EC2Remediation"
        Effect = "Allow"
        Action = [
          "ec2:CreateSnapshot",
          "ec2:DescribeVolumes",
          "ec2:DescribeInstances",
          "ec2:ModifyInstanceAttribute",
          "ec2:CreateSecurityGroup",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupEgress",
          "ec2:ReplaceNetworkAclAssociation"
        ]
        Resource = "*"
      },
      {
        Sid    = "RDSRemediation"
        Effect = "Allow"
        Action = [
          "rds:ModifyDBInstance",
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      },
      {
        Sid    = "Notifications"
        Effect = "Allow"
        Action = ["sns:Publish"]
        Resource = [aws_sns_topic.security_alerts.arn]
      },
      {
        Sid    = "SecurityHubUpdate"
        Effect = "Allow"
        Action = [
          "securityhub:BatchUpdateFindings"
        ]
        Resource = "*"
      },
      {
        Sid    = "Logging"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Sid      = "XRay"
        Effect   = "Allow"
        Action   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
        Resource = "*"
      }
    ]
  })
}

# --- Alert Forwarder Lambda Role ---
resource "aws_iam_role" "alert_lambda" {
  name = "${var.project_name}-alert-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "alert_lambda" {
  name = "${var.project_name}-alert-policy"
  role = aws_iam_role.alert_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [aws_sns_topic.security_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
        Resource = "*"
      }
    ]
  })
}

# --- Compliance Reporter Lambda Role ---
resource "aws_iam_role" "reporter_lambda" {
  name = "${var.project_name}-reporter-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "reporter_lambda" {
  name = "${var.project_name}-reporter-policy"
  role = aws_iam_role.reporter_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecurityHubRead"
        Effect = "Allow"
        Action = [
          "securityhub:GetFindings",
          "securityhub:GetInsights",
          "securityhub:DescribeStandards",
          "securityhub:GetEnabledStandards",
          "securityhub:DescribeStandardsControls"
        ]
        Resource = "*"
      },
      {
        Sid    = "ConfigRead"
        Effect = "Allow"
        Action = [
          "config:DescribeComplianceByConfigRule",
          "config:GetComplianceDetailsByConfigRule",
          "config:DescribeConfigRules"
        ]
        Resource = "*"
      },
      {
        Sid      = "ReportStorage"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.reports.arn}/*"
      },
      {
        Sid      = "KMS"
        Effect   = "Allow"
        Action   = ["kms:GenerateDataKey", "kms:Decrypt"]
        Resource = [aws_kms_key.security.arn]
      },
      {
        Sid      = "Notifications"
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [aws_sns_topic.security_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
        Resource = "*"
      }
    ]
  })
}
