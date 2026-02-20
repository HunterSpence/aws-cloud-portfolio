###############################################################################
# AWS Security Hub — Centralized Security Findings
###############################################################################

resource "aws_securityhub_account" "this" {}

# CIS AWS Foundations Benchmark v1.4.0
resource "aws_securityhub_standards_subscription" "cis" {
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.4.0"
  depends_on    = [aws_securityhub_account.this]
}

# AWS Foundational Security Best Practices v1.0.0
resource "aws_securityhub_standards_subscription" "aws_foundational" {
  standards_arn = "arn:aws:securityhub:${data.aws_region.current.name}::standards/aws-foundational-security-best-practices/v/1.0.0"
  depends_on    = [aws_securityhub_account.this]
}

# NIST 800-53 Rev 5
resource "aws_securityhub_standards_subscription" "nist" {
  standards_arn = "arn:aws:securityhub:${data.aws_region.current.name}::standards/nist-800-53/v/5.0.0"
  depends_on    = [aws_securityhub_account.this]
}

data "aws_region" "current" {}

# Auto-enable new controls
resource "aws_securityhub_finding_aggregator" "this" {
  count        = var.enable_finding_aggregator ? 1 : 0
  linking_mode = "ALL_REGIONS"
  depends_on   = [aws_securityhub_account.this]
}

# EventBridge rule for critical/high findings
resource "aws_cloudwatch_event_rule" "securityhub_findings" {
  name        = "${var.project_name}-securityhub-critical"
  description = "Capture Security Hub critical and high severity findings"

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

  tags = var.tags
}
