terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Provider para recursos en us-east-1 (requerido para ACM + CloudFront)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
