variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name used in tags."
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "inventory-eks"
}

variable "cluster_version" {
  description = "EKS Kubernetes version. Pick one still in standard support (extended support costs 6x)."
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.30.0.0/16"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group (m7i-flex.large is allowed on the AWS Free plan)."
  type        = list(string)
  default     = ["m7i-flex.large"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 3
}

variable "github_repository" {
  description = "GitHub repo (owner/name) allowed to deploy via OIDC. Empty string disables the deploy role."
  type        = string
  default     = ""
}

variable "github_oidc_subject_prefix" {
  description = <<-EOT
    The repo's OIDC subject prefix when GitHub uses immutable subjects, e.g.
    "repo:Owner@123/name@456". Get it with:
    gh api repos/<owner>/<repo>/actions/oidc/customization/sub --jq .sub_claim_prefix
    Leave empty for the classic "repo:<owner>/<repo>" format.
  EOT
  type        = string
  default     = ""
}

variable "create_github_oidc_provider" {
  description = "Create the GitHub Actions OIDC provider. Set false if your AWS account already has one."
  type        = bool
  default     = true
}
