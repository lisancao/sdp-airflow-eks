# Remote state so any authorized machine (laptop, Omnigent, CI) operates
# the same infrastructure. S3-native locking (Terraform >= 1.10) — no
# DynamoDB table needed.
terraform {
  backend "s3" {
    bucket       = "sdp-airflow-tfstate-49149b06"
    key          = "sdp-airflow/terraform.tfstate"
    region       = "us-west-2"
    use_lockfile = true
  }
}
