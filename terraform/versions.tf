terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95"
    }
  }

  # State is local by default. For a team, move it to S3 with a lock, e.g.:
  # backend "s3" {
  #   bucket       = "my-tf-state-bucket"
  #   key          = "inventory/eks.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "inventory-manager"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
