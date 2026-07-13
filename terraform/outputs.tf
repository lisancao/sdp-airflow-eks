output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "region" {
  value = var.aws_region
}

output "pipeline_bucket" {
  description = "S3 bucket for SDP pipeline storage — set this in pipelines/spark-pipeline.yml and k8s/spark/configmap.yaml"
  value       = aws_s3_bucket.pipeline.bucket
}

output "spark_irsa_role_arn" {
  description = "Annotate the spark service account with this role"
  value       = module.spark_irsa.iam_role_arn
}

output "airflow_irsa_role_arn" {
  description = "Annotate the airflow worker/scheduler service accounts with this role"
  value       = module.airflow_irsa.iam_role_arn
}

output "allowed_cidrs" {
  value = var.allowed_cidrs
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}
