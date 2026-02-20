# =============================================================================
# Aurora PostgreSQL — Multi-AZ with Read Replica, Encryption, Automated Backups
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}"
  subnet_ids = var.private_subnet_ids
  tags       = merge(var.tags, { Name = "${var.project_name}-db-subnet-group" })
}

resource "aws_rds_cluster" "main" {
  cluster_identifier     = "${var.project_name}-${var.environment}"
  engine                 = "aurora-postgresql"
  engine_version         = "15.4"
  database_name          = var.db_name
  master_username        = var.db_master_username
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  # Encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.db.arn

  # Backups
  backup_retention_period = var.db_backup_retention
  preferred_backup_window = "03:00-04:00"
  copy_tags_to_snapshot   = true

  # Maintenance
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  apply_immediately            = false

  # Protection
  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment == "production" ? false : true
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final"

  # Logging
  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = merge(var.tags, { Name = "${var.project_name}-aurora-cluster" })
}

# Primary instance
resource "aws_rds_cluster_instance" "primary" {
  identifier         = "${var.project_name}-${var.environment}-primary"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = merge(var.tags, { Name = "${var.project_name}-primary" })
}

# Read replica
resource "aws_rds_cluster_instance" "replica" {
  identifier         = "${var.project_name}-${var.environment}-replica"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = merge(var.tags, { Name = "${var.project_name}-replica" })
}

# KMS key for encryption
resource "aws_kms_key" "db" {
  description             = "KMS key for ${var.project_name} Aurora encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = var.tags
}

resource "aws_kms_alias" "db" {
  name          = "alias/${var.project_name}-${var.environment}-db"
  target_key_id = aws_kms_key.db.key_id
}

# Security group
resource "aws_security_group" "db" {
  name_prefix = "${var.project_name}-db-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.app_security_group_ids
    description     = "PostgreSQL from app tier"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-db-sg" })
}

# Enhanced monitoring IAM role
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
