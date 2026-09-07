variable "name" {
  description = "Cloud Run service name (also used for its service account)."
  type        = string
}

variable "location" {
  type = string
}

variable "image" {
  description = "Artifact Registry image URI."
  type        = string
}

variable "health_path" {
  description = "HTTP path probed at startup."
  type        = string
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "env" {
  description = "Plain environment variables."
  type        = map(string)
  default     = {}
}

variable "secret_env" {
  description = "Environment variables sourced from Secret Manager: ENV_NAME => secret id."
  type        = map(string)
  default     = {}
}

variable "vpc_connector" {
  description = "Serverless VPC Access connector id, or null when the service needs no private egress."
  type        = string
  default     = null
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "1Gi"
}

variable "min_instances" {
  type    = number
  default = 0
}

variable "max_instances" {
  type    = number
  default = 2
}

variable "public" {
  description = "Allow unauthenticated invocations."
  type        = bool
  default     = true
}
