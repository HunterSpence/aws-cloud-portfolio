output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs"
}

output "nat_gateway_ids" {
  value       = aws_nat_gateway.main[*].id
  description = "NAT Gateway IDs"
}

output "vpc_cidr_block" {
  value       = aws_vpc.main.cidr_block
  description = "VPC CIDR block"
}
