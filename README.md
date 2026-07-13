# sdp-airflow-eks

Self-hosted **Apache Airflow 3 + Spark Declarative Pipelines (Spark 4.1)** on
Amazon EKS. Airflow schedules; SDP owns the dataflow graph; a long-running
Spark Connect server executes pipelines on a standalone Spark cluster inside
Kubernetes.

```
                       ┌─────────────────────── EKS ───────────────────────┐
  users ──ALB (HTTP,   │  airflow ns                    spark ns           │
  CIDR-gated, per-user │  ┌──────────────┐   sc://      ┌───────────────┐  │
  credentials)──────────▶ │ api-server   │  :15002      │ spark-connect │  │
                       │  │ scheduler    ├─────────────▶│      │        │  │
                       │  │ dag-processor│              │ spark-master  │  │
                       │  │ task pods    │              │ spark-workers │  │
                       │  └──────┬───────┘              └───────┬───────┘  │
                       │         │ git-sync (this repo)         │ s3a      │
                       └─────────┼──────────────────────────────┼──────────┘
                                 ▼                              ▼
                            github.com                   S3 (pipeline storage)
```

## What's in here

| Path | What |
|------|------|
| `terraform/` | VPC, EKS, S3 pipeline bucket, IRSA roles, AWS Load Balancer Controller |
| `k8s/spark/` | Spark 4.1 master, workers, and Connect server manifests |
| `k8s/airflow-values.yaml` | Official Airflow Helm chart values (Airflow 3, KubernetesExecutor, git-sync, ALB ingress) |
| `docker/airflow/` | Airflow image with `pyspark[connect]` (built to GHCR by CI) |
| `dags/` | SDP DAGs + vendored `SparkPipelinesOperator` |
| `pipelines/` | The declarative pipeline: spec + transformations |
| `scripts/create-users.sh` | Mint per-person access tokens |

## Deploy

Prereqs: `aws` (authenticated), `terraform >= 1.5`, `kubectl`, `helm`.

```bash
# 1. Infrastructure (~20 min)
cp terraform/example.tfvars terraform/terraform.tfvars   # edit allowed_cidrs!
make infra
make kubeconfig

# 2. Fill in the generated values
terraform -chdir=terraform output    # bucket name + IRSA role ARNs
# - REPLACE_PIPELINE_BUCKET in k8s/spark/configmap.yaml and pipelines/spark-pipeline.yml
# - IRSA role ARNs in k8s/spark/namespace.yaml and k8s/airflow-values.yaml

# 3. Apps
make deploy-spark
make deploy-airflow

# 4. Access
make users     # generates per-person tokens (edit USERS in the script first)
make url       # ALB address for the Airflow UI
```

Commit and push the bucket/ARN edits — DAGs and pipeline code reach the
cluster via git-sync from `main`, so the repo is the deploy artifact.

## Access model

Two gates, both cheap to operate:

1. **Network**: the ALB only accepts traffic from `allowed_cidrs`
   (Terraform) / `inbound-cidrs` (ingress annotation). Set these to your
   users' networks; keep `0.0.0.0/0` only if you accept a public login page.
2. **Credentials**: `scripts/create-users.sh` creates named Airflow users
   with generated 32-char tokens. Revoke one person without touching the
   rest. Delete the bootstrap `admin` user after minting real ones.

The ALB terminates plain HTTP by default (no domain required). If you have
a domain, add an ACM cert and switch the listener annotation to HTTPS —
worth it before sharing credentials broadly.

## Cost (rough, us-west-2)

| Item | ~$/mo |
|------|-------|
| EKS control plane | 73 |
| 2× m6a.xlarge nodes | 250 |
| NAT gateway + ALB | 50 |
| **Total** | **~$375** |

Scale the node group down (`node_group_desired = 1`, smaller instances) for
a lighter footprint. `make destroy` tears everything down.

## Local development

The same stack runs locally via docker compose in
[lakehouse-stack](https://github.com/lisancao/lakehouse-stack) — this repo is
the remote/EKS deployment of the same Airflow ↔ SDP wiring.
