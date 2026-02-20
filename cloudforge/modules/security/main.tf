# =============================================================================
# CloudForge — Security Module
# =============================================================================
# Manages security group rules, KMS encryption keys, and SSM Parameter Store
# entries for secrets management. Follows AWS Well-Architected security pillar.
# =============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# -----------------------------------------------------------------------------
# KMS — Encryption Keys
# -----------------------------------------------------------------------------

# Primary encryption key for application secrets (RDS, SSM, S3, EBS)
resource "aws_kms_key" "main" {
  description             = "${local.name_prefix} primary encryption key"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms_policy.json
  tags                    = var.tags
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name_prefix}-main"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "kms_policy" {
  # Allow root account full access
  statement {
    sid       = "EnableRootAccountAccess"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  # Allow CloudWatch Logs encryption
  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["logs.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

# -----------------------------------------------------------------------------
# Security Groups — Baseline Rules
# -----------------------------------------------------------------------------

# ALB security group — public HTTPS ingress
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"
  description = "Allow HTTPS ingress to ALB"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${local.name_prefix}-alb-sg" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTPS from internet"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
  tags              = var.tags
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from internet (redirect to HTTPS)"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
  tags              = var.tags
}

resource "aws_vpc_security_group_egress_rule" "alb_egress" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow all outbound"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
  tags              = var.tags
}

# Application security group — only from ALB
resource "aws_security_group" "app" {
  name_prefix = "${local.name_prefix}-app-"
  description = "Allow traffic from ALB to ECS tasks"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${local.name_prefix}-app-sg" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  description                  = "Traffic from ALB"
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
  referenced_security_group_id = aws_security_group.alb.id
  tags                         = var.tags
}

resource "aws_vpc_security_group_egress_rule" "app_egress" {
  security_group_id = aws_security_group.app.id
  description       = "Allow all outbound (ECR, secrets, etc.)"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
  tags              = var.tags
}

# Database security group — only from app
resource "aws_security_group" "database" {
  name_prefix = "${local.name_prefix}-db-"
  description = "Allow PostgreSQL from application tier only"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${local.name_prefix}-db-sg" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "db_from_app" {
  security_group_id            = aws_security_group.database.id
  description                  = "PostgreSQL from app tier"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = aws_security_group.app.id
  tags                         = var.tags
}

# -----------------------------------------------------------------------------
# SSM Parameter Store — Secrets Management
# -----------------------------------------------------------------------------

resource "aws_ssm_parameter" "db_password" {
  name        = "/${local.name_prefix}/database/master-password"
  description = "Aurora PostgreSQL master password"
  type        = "SecureString"
  key_id      = aws_kms_key.main.arn
  value       = var.db_master_password

  tags = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "app_secrets" {
  for_each = var.app_secrets

  name        = "/${local.name_prefix}/app/${each.key}"
  description = "Application secret: ${each.key}"
  type        = "SecureString"
  key_id      = aws_kms_key.main.arn
  value       = each.value

  tags = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}
