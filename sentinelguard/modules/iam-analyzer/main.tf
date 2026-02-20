###############################################################################
# IAM Access Analyzer — Identify Unintended Resource Access
###############################################################################

resource "aws_accessanalyzer_analyzer" "account" {
  analyzer_name = "${var.project_name}-account-analyzer"
  type          = "ACCOUNT"
  tags          = var.tags
}

resource "aws_accessanalyzer_analyzer" "organization" {
  count         = var.enable_org_analyzer ? 1 : 0
  analyzer_name = "${var.project_name}-org-analyzer"
  type          = "ORGANIZATION"
  tags          = var.tags
}

# EventBridge rule for Access Analyzer findings
resource "aws_cloudwatch_event_rule" "access_analyzer" {
  name        = "${var.project_name}-access-analyzer-findings"
  description = "Capture IAM Access Analyzer findings"

  event_pattern = jsonencode({
    source      = ["aws.access-analyzer"]
    detail-type = ["Access Analyzer Finding"]
    detail = {
      status = ["ACTIVE"]
    }
  })

  tags = var.tags
}

# Archive rule for known trusted access
resource "aws_accessanalyzer_archive_rule" "trusted_accounts" {
  count         = length(var.trusted_account_ids) > 0 ? 1 : 0
  analyzer_name = aws_accessanalyzer_analyzer.account.analyzer_name
  rule_name     = "trusted-accounts"

  filter {
    criteria = "principal.AWS"
    contains = var.trusted_account_ids
  }
}
