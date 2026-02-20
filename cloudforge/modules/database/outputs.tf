output "cluster_endpoint" { value = aws_rds_cluster.main.endpoint }
output "reader_endpoint" { value = aws_rds_cluster.main.reader_endpoint }
output "cluster_id" { value = aws_rds_cluster.main.id }
output "db_security_group_id" { value = aws_security_group.db.id }
