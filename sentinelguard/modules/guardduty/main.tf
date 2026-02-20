###############################################################################
# Amazon GuardDuty — Threat Detection
###############################################################################

resource "aws_guardduty_detector" "this" {
  enable                       = true
  finding_publishing_frequency = var.publishing_frequency

  datasources {
    s3_logs {
      enable = true
    }

    kubernetes {
      audit_logs {
        enable = var.enable_eks_protection
      }
    }

    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = var.tags
}

# SNS topic for GuardDuty findings
resource "aws_sns_topic" "guardduty_alerts" {
  name              = "${var.project_name}-guardduty-alerts"
  kms_master_key_id = var.sns_kms_key_id
  tags              = var.tags
}

# EventBridge rule for high/critical findings
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "${var.project_name}-guardduty-findings"
  description = "Capture GuardDuty findings with medium severity or higher"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [{ numeric = [">=", 4] }]
    }
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "guardduty_sns" {
  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "guardduty-to-sns"
  arn       = aws_sns_topic.guardduty_alerts.arn
}

resource "aws_sns_topic_policy" "guardduty_alerts" {
  arn = aws_sns_topic.guardduty_alerts.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowEventBridgePublish"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "SNS:Publish"
      Resource  = aws_sns_topic.guardduty_alerts.arn
    }]
  })
}
