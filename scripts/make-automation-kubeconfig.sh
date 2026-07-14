#!/usr/bin/env bash
# Emit a standalone kubeconfig for the `automation` ServiceAccount.
# Output file is gitignored (kubeconfig*). Hand it to the agent/CI that
# needs cluster access — no AWS credentials involved.
set -euo pipefail

CTX="${CTX:?set CTX to your kubectl context arn}"
OUT="${1:-kubeconfig-automation}"

SERVER=$(kubectl --context "$CTX" config view --minify -o jsonpath='{.clusters[0].cluster.server}')
CA=$(kubectl --context "$CTX" -n kube-system get secret automation-token -o jsonpath='{.data.ca\.crt}')
TOKEN=$(kubectl --context "$CTX" -n kube-system get secret automation-token -o jsonpath='{.data.token}' | base64 -d)

cat > "$OUT" <<EOF
apiVersion: v1
kind: Config
clusters:
  - name: sdp-airflow
    cluster:
      server: ${SERVER}
      certificate-authority-data: ${CA}
users:
  - name: automation
    user:
      token: ${TOKEN}
contexts:
  - name: sdp-airflow-automation
    context: {cluster: sdp-airflow, user: automation}
current-context: sdp-airflow-automation
EOF

chmod 600 "$OUT"
echo "wrote $OUT (mode 600). Test: kubectl --kubeconfig $OUT get ns"
