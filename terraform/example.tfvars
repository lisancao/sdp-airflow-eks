# Copy to terraform.tfvars and adjust.
aws_region         = "us-west-2"
cluster_name       = "sdp-airflow"
kubernetes_version = "1.31"

node_instance_types = ["m6a.xlarge"]
node_group_min      = 2
node_group_max      = 4
node_group_desired  = 2

# Lock the ALB down to the networks your 3-5 users actually sit on.
# Find yours with: curl -s ifconfig.me
allowed_cidrs = [
  # "203.0.113.7/32",  # you
  # "198.51.100.0/24", # office
  "0.0.0.0/0",
]
