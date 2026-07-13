#!/usr/bin/env bash
# Mint per-person access credentials for the Airflow UI/API.
#
# Each user gets a generated 32-char token as their password — treat the
# token as the access key. Credentials print once and are written to a
# local gitignored file; distribute them out-of-band and rotate by
# re-running with a new token (or delete the user).
set -euo pipefail

NAMESPACE="${AIRFLOW_NS:-airflow}"
ROLE="${AIRFLOW_ROLE:-User}"   # User = trigger/view DAGs; Admin only for you

# Edit this list: username:email, 3-5 people.
USERS=(
  "lisa:lisanatashacao@gmail.com"
  # "friend1:friend1@example.com"
  # "friend2:friend2@example.com"
)

POD=$(kubectl -n "$NAMESPACE" get pod -l component=api-server \
  -o jsonpath='{.items[0].metadata.name}')
OUT="credentials-$(date +%Y%m%d-%H%M%S).txt"

for entry in "${USERS[@]}"; do
  user="${entry%%:*}"
  email="${entry##*:}"
  token=$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)

  kubectl -n "$NAMESPACE" exec "$POD" -- airflow users create \
    --username "$user" \
    --password "$token" \
    --firstname "$user" \
    --lastname "-" \
    --role "$ROLE" \
    --email "$email" >/dev/null

  echo "$user  $token" | tee -a "$OUT"
done

echo
echo "Credentials saved to $OUT (gitignored). Distribute out-of-band."
echo "Now rotate or delete the bootstrap admin:"
echo "  kubectl -n $NAMESPACE exec $POD -- airflow users delete --username admin"
