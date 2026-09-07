variable "name" {
  description = "Service name; prefixes every resource created here."
  type        = string
}

variable "region" {
  type = string
}

variable "cluster_id" {
  type = string
}

variable "image" {
  description = "ECR image URI."
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
  description = "Environment variables sourced from Secrets Manager: ENV_NAME => secret ARN."
  type        = map(string)
  default     = {}
}

variable "subnets" {
  type = list(string)
}

variable "security_groups" {
  type = list(string)
}

variable "target_group_arn" {
  description = "ALB target group this service registers into."
  type        = string
}

variable "cpu" {
  type    = string
  default = "512"
}

variable "memory" {
  type    = string
  default = "1024"
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "log_retention_days" {
  type    = number
  default = 14
}
