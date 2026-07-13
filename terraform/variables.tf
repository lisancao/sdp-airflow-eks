variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "sdp-airflow"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.31"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.42.0.0/16"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["m6a.xlarge"]
}

variable "node_group_min" {
  description = "Minimum nodes"
  type        = number
  default     = 2
}

variable "node_group_max" {
  description = "Maximum nodes"
  type        = number
  default     = 4
}

variable "node_group_desired" {
  description = "Desired nodes"
  type        = number
  default     = 2
}

variable "allowed_cidrs" {
  description = <<-EOT
    CIDR blocks allowed to reach the public Airflow ALB. This is the outer
    access gate; leave as 0.0.0.0/0 only if you accept a fully public
    login page protected by Airflow credentials alone.
  EOT
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "pipeline_bucket_prefix" {
  description = "Prefix for the S3 bucket holding SDP pipeline storage (a random suffix is appended)"
  type        = string
  default     = "sdp-pipeline-storage"
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "sdp-airflow-eks"
    ManagedBy = "terraform"
  }
}
