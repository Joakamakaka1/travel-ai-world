output "artifact_registry_repository" {
  value = google_artifact_registry_repository.backend.name
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend.repository_id}"
}

output "core_api_url" {
  description = "Public URL of core_api — the frontend's NEXT_PUBLIC_API_URL."
  value       = module.core_api.uri
}

output "ai_api_url" {
  description = "Public URL of ai_api — the frontend's NEXT_PUBLIC_AI_API_URL."
  value       = module.ai_api.uri
}

output "cloud_sql_private_ip" {
  value = google_sql_database_instance.main.private_ip_address
}

output "cloud_sql_connection_name" {
  value = google_sql_database_instance.main.connection_name
}
