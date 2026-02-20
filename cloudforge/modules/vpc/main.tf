# =============================================================================
# CloudForge — VPC Module
# =============================================================================
# Creates a production-grade VPC across 3 Availability Zones with:
#   - Public subnets (ALB, NAT Gateways, bastion hosts)
#   - Private subnets (ECS tasks, application tier)
#   - Database subnets (Aurora, isolated from internet)
#   - NAT Gateways for outbound internet from private subnets
#   - VPC Flow Logs for network visibility and compliance
# =============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Subnet CIDR calculation — /20 subnets within the /16 VPC
  # Public:   10.0.0.0/20, 10.0.16.0/20, 10.0.32.0/20
  # Private:  10.0.48.0/20, 10.0.64.0/20, 10.0.80.0/20
  # Database: 10.0.96.0/20, 10.0.112.0/20, 10.0.128.0/20
  public_subnets   = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, i)]
  private_subnets  = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, i + 3)]
  database_subnets = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, i + 6)]
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# -----------------------------------------------------------------------------
# Internet Gateway — provides internet access to public subnets
# -----------------------------------------------------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-igw"
  })
}

# -----------------------------------------------------------------------------
# Public Subnets — one per AZ for ALB and NAT Gateways
# -----------------------------------------------------------------------------
resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-public-${var.availability_zones[count.index]}"
    Tier = "public"
  })
}

# -----------------------------------------------------------------------------
# Private Subnets — one per AZ for ECS Fargate tasks
# -----------------------------------------------------------------------------
resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnets[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-private-${var.availability_zones[count.index]}"
    Tier = "private"
  })
}

# -----------------------------------------------------------------------------
# Database Subnets — isolated, no route to internet
# -----------------------------------------------------------------------------
resource "aws_subnet" "database" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.database_subnets[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-database-${var.availability_zones[count.index]}"
    Tier = "database"
  })
}

# -----------------------------------------------------------------------------
# Database Subnet Group — required by RDS/Aurora
# -----------------------------------------------------------------------------
resource "aws_db_subnet_group" "database" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

# -----------------------------------------------------------------------------
# Elastic IPs for NAT Gateways
# -----------------------------------------------------------------------------
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-nat-eip-${count.index}"
  })
}

# -----------------------------------------------------------------------------
# NAT Gateways — placed in public subnets, one per AZ for HA
# (or single for cost savings in non-production)
# -----------------------------------------------------------------------------
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-nat-${count.index}"
  })

  depends_on = [aws_internet_gateway.main]
}

# -----------------------------------------------------------------------------
# Route Tables — Public
# -----------------------------------------------------------------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# -----------------------------------------------------------------------------
# Route Tables — Private (one per AZ for HA NAT routing)
# -----------------------------------------------------------------------------
resource "aws_route_table" "private" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-private-rt-${count.index}"
  })
}

resource "aws_route" "private_nat" {
  count = var.enable_nat_gateway ? length(var.availability_zones) : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}

resource "aws_route_table_association" "private" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# -----------------------------------------------------------------------------
# Route Tables — Database (no internet route = fully isolated)
# -----------------------------------------------------------------------------
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-database-rt"
  })
}

resource "aws_route_table_association" "database" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# -----------------------------------------------------------------------------
# VPC Flow Logs — captures all traffic for security auditing
# Sent to CloudWatch Logs for analysis and alerting
# -----------------------------------------------------------------------------
resource "aws_flow_log" "vpc" {
  vpc_id                   = aws_vpc.main.id
  traffic_type             = "ALL"
  log_destination_type     = "cloud-watch-logs"
  log_destination          = aws_cloudwatch_log_group.flow_logs.arn
  iam_role_arn             = aws_iam_role.flow_logs.arn
  max_aggregation_interval = 60

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-flow-logs"
  })
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/flow-logs/${local.name_prefix}"
  retention_in_days = 30

  tags = var.tags
}

resource "aws_iam_role" "flow_logs" {
  name = "${local.name_prefix}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "flow_logs" {
  name = "${local.name_prefix}-flow-logs-policy"
  role = aws_iam_role.flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}
