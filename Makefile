SHELL := /bin/bash
AWS_REGION ?= us-west-2
CLUSTER_NAME ?= sdp-airflow
AIRFLOW_NS ?= airflow
SPARK_NS ?= spark

.PHONY: help infra kubeconfig deploy-spark deploy-airflow users url destroy

help:
	@grep -E '^[a-z-]+:' Makefile | sed 's/:.*//' | sort

infra: ## Provision VPC + EKS + S3 + ALB controller
	cd terraform && terraform init && terraform apply

kubeconfig: ## Point kubectl at the cluster
	aws eks update-kubeconfig --region $(AWS_REGION) --name $(CLUSTER_NAME)

deploy-spark: ## Deploy Spark master, workers, and Connect server
	kubectl apply -f k8s/spark/namespace.yaml
	kubectl -n $(SPARK_NS) apply -f k8s/spark/

deploy-airflow: ## Install/upgrade Airflow via the official Helm chart
	helm repo add apache-airflow https://airflow.apache.org 2>/dev/null || true
	helm repo update apache-airflow
	helm upgrade --install airflow apache-airflow/airflow \
		--namespace $(AIRFLOW_NS) --create-namespace \
		-f k8s/airflow-values.yaml \
		$(shell [ -f k8s/airflow-values.local.yaml ] && echo "-f k8s/airflow-values.local.yaml") \
		--timeout 15m

users: ## Generate access tokens for named users (edit USERS in the script)
	./scripts/create-users.sh

url: ## Print the Airflow UI address
	@kubectl -n $(AIRFLOW_NS) get ingress airflow-ingress \
		-o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'

destroy: ## Tear everything down (deletes the ALB first so TF can finish)
	-helm uninstall airflow -n $(AIRFLOW_NS)
	-kubectl delete -f k8s/spark/ -n $(SPARK_NS) --ignore-not-found
	cd terraform && terraform destroy
