output "ecr_repository_urls" {
  description = "ECR repository URL per service image."
  value       = { for k, r in aws_ecr_repository.services : k => r.repository_url }
}

output "aws_region" {
  value = var.region
}

output "load_balancer_dns_name" {
  value = aws_lb.backend.dns_name
}

output "backend_url" {
  description = "Single public origin: core_api by default, /api/v1/ai/* routed to ai_api."
  value       = "http://${aws_lb.backend.dns_name}"
}

output "rds_endpoint" {
  value = aws_db_instance.main.address
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}
