###############################################################################
# AWS Config Recorder & Delivery Channel
###############################################################################

resource "aws_config_configuration_recorder" "this" {
  name     = "${var.project_name}-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "this" {
  name           = "${var.project_name}-delivery"
  s3_bucket_name = var.config_s3_bucket

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.this]
}

resource "aws_config_configuration_recorder_status" "this" {
  name       = aws_config_configuration_recorder.this.name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.this]
}

###############################################################################
# IAM Role for Config
###############################################################################

resource "aws_iam_role" "config" {
  name = "${var.project_name}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "config.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

###############################################################################
# CIS Benchmark — AWS Config Managed Rules (16 rules)
###############################################################################

# 1. S3 bucket public read prohibited
resource "aws_config_config_rule" "s3_bucket_public_read_prohibited" {
  name = "s3-bucket-public-read-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 2. S3 bucket public write prohibited
resource "aws_config_config_rule" "s3_bucket_public_write_prohibited" {
  name = "s3-bucket-public-write-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_WRITE_PROHIBITED"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 3. S3 bucket server-side encryption enabled
resource "aws_config_config_rule" "s3_bucket_ssl_requests_only" {
  name = "s3-bucket-ssl-requests-only"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SSL_REQUESTS_ONLY"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 4. Root account MFA enabled
resource "aws_config_config_rule" "root_account_mfa_enabled" {
  name = "root-account-mfa-enabled"
  source {
    owner             = "AWS"
    source_identifier = "ROOT_ACCOUNT_MFA_ENABLED"
  }
  maximum_execution_frequency = "TwentyFour_Hours"
  depends_on                  = [aws_config_configuration_recorder.this]
}

# 5. IAM root access key check
resource "aws_config_config_rule" "iam_root_access_key_check" {
  name = "iam-root-access-key-check"
  source {
    owner             = "AWS"
    source_identifier = "IAM_ROOT_ACCESS_KEY_CHECK"
  }
  maximum_execution_frequency = "TwentyFour_Hours"
  depends_on                  = [aws_config_configuration_recorder.this]
}

# 6. MFA enabled for IAM console access
resource "aws_config_config_rule" "mfa_enabled_for_iam_console_access" {
  name = "mfa-enabled-for-iam-console-access"
  source {
    owner             = "AWS"
    source_identifier = "MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS"
  }
  maximum_execution_frequency = "TwentyFour_Hours"
  depends_on                  = [aws_config_configuration_recorder.this]
}

# 7. IAM password policy
resource "aws_config_config_rule" "iam_password_policy" {
  name = "iam-password-policy"
  source {
    owner             = "AWS"
    source_identifier = "IAM_PASSWORD_POLICY"
  }
  input_parameters = jsonencode({
    RequireUppercaseCharacters = "true"
    RequireLowercaseCharacters = "true"
    RequireSymbols             = "true"
    RequireNumbers             = "true"
    MinimumPasswordLength      = "14"
    PasswordReusePrevention    = "24"
    MaxPasswordAge             = "90"
  })
  maximum_execution_frequency = "TwentyFour_Hours"
  depends_on                  = [aws_config_configuration_recorder.this]
}

# 8. CloudTrail enabled
resource "aws_config_config_rule" "cloudtrail_enabled" {
  name = "cloudtrail-enabled"
  source {
    owner             = "AWS"
    source_identifier = "CLOUD_TRAIL_ENABLED"
  }
  maximum_execution_frequency = "TwentyFour_Hours"
  depends_on                  = [aws_config_configuration_recorder.this]
}

# 9. CloudTrail log file validation enabled
resource "aws_config_config_rule" "cloudtrail_log_file_validation" {
  name = "cloud-trail-log-file-validation-enabled"
  source {
    owner             = "AWS"
    source_identifier = "CLOUD_TRAIL_LOG_FILE_VALIDATION_ENABLED"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 10. Encrypted volumes
resource "aws_config_config_rule" "encrypted_volumes" {
  name = "encrypted-volumes"
  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 11. RDS storage encrypted
resource "aws_config_config_rule" "rds_storage_encrypted" {
  name = "rds-storage-encrypted"
  source {
    owner             = "AWS"
    source_identifier = "RDS_STORAGE_ENCRYPTED"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 12. VPC flow logs enabled
resource "aws_config_config_rule" "vpc_flow_logs_enabled" {
  name = "vpc-flow-logs-enabled"
  source {
    owner             = "AWS"
    source_identifier = "VPC_FLOW_LOGS_ENABLED"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 13. Restricted incoming traffic (SSH)
resource "aws_config_config_rule" "restricted_ssh" {
  name = "restricted-ssh"
  source {
    owner             = "AWS"
    source_identifier = "INCOMING_SSH_DISABLED"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 14. Restricted common ports
resource "aws_config_config_rule" "restricted_common_ports" {
  name = "restricted-common-ports"
  source {
    owner             = "AWS"
    source_identifier = "RESTRICTED_INCOMING_TRAFFIC"
  }
  input_parameters = jsonencode({
    blockedPort1 = "3389"
    blockedPort2 = "3306"
    blockedPort3 = "1433"
    blockedPort4 = "5432"
  })
  depends_on = [aws_config_configuration_recorder.this]
}

# 15. CloudWatch log group encrypted
resource "aws_config_config_rule" "cloudwatch_log_group_encrypted" {
  name = "cloudwatch-log-group-encrypted"
  source {
    owner             = "AWS"
    source_identifier = "CW_LOGGROUP_RETENTION_PERIOD_CHECK"
  }
  depends_on = [aws_config_configuration_recorder.this]
}

# 16. Multi-region CloudTrail enabled
resource "aws_config_config_rule" "multi_region_cloudtrail" {
  name = "multi-region-cloud-trail-enabled"
  source {
    owner             = "AWS"
    source_identifier = "MULTI_REGION_CLOUD_TRAIL_ENABLED"
  }
  maximum_execution_frequency = "TwentyFour_Hours"
  depends_on                  = [aws_config_configuration_recorder.this]
}
