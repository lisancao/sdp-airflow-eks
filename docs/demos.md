# Demo runbook

Every demo below runs against the live EKS environment. Shorthand used
throughout:

```bash
export CTX="arn:aws:eks:us-west-2:207734640204:cluster/sdp-airflow"   # adjust to your cluster
alias k='kubectl --context $CTX'
```

**Surfaces to have open:**
- Airflow UI — https://airflow.systemsnull.net (or the ALB URL)
- Spark UI — https://spark.systemsnull.net (basic auth; every Spark query shows in the SQL tab)
- Terminal with `k9s --context $CTX -n airflow` (watch task pods live)

---

## 1. Imperative vs declarative (the flagship)

Same bronze→silver→gold events flow, two philosophies.

1. Open both DAG graph views side by side: `medallion_imperative` (4 boxes,
   hand-wired) vs `sdp_events_pipeline` (1 box; the graph lives in
   `pipelines/spark-pipeline.yml`).
2. Trigger both. In k9s watch 4 pods spawn sequentially vs 1.
3. Open the SDP task log: the runtime reports per-flow progress
   (`raw_events COMPLETED → clean_events RUNNING → …`) inside one task.
4. Punchline numbers: ~85s vs ~35s, 4 sessions vs 1, and the imperative
   DAG's wiring line (`create_schema() >> bronze… >> gold…`) that a human
   must maintain.

## 2. The dry-run gate (CI for data)

`sdp_validate_then_run` validates the graph before executing.

- Green path: trigger with no config → validate passes → run executes.
- Gate path: trigger with config:
  ```json
  {"spec_path": "/opt/airflow/dags/repo/pipelines/broken/spark-pipeline.yml"}
  ```
  The broken pipeline reads a table nothing produces. Dry-run fails in
  seconds, the run task shows `upstream_failed`, no data was touched.
  Task log shows the exact unresolved reference.

## 3. Event-driven ingestion

`s3_event_pipeline` — a file landing in S3 triggers the run.

```bash
# 1. Trigger the DAG; the sensor polls s3://…/incoming/ every 30s
# 2. Land a file:
aws s3 cp README.md s3://sdp-pipeline-storage-68729b89/incoming/demo.json
# 3. Sensor flips green → pipeline runs → cleanup task deletes the marker
```

## 4. Push-to-deploy

The repo is the deploy artifact — no build, no kubectl.

```bash
# change a transformation, e.g. add a column to events_summary
vim pipelines/transformations/events.py
git commit -am "demo: add avg_amount" && git push
# git-sync pulls within 60s; trigger sdp_events_pipeline; the new column is live
```

## 5. Live scale-out

```bash
k -n spark scale deploy/spark-worker --replicas=4
```

Watch the Spark master UI executors join within ~30s, then run a
pipeline. Scale back with `--replicas=2` (each worker ≈ 2 cores / 4 GB —
watch node headroom before going higher).

## 6. Failure recovery

The catalog lives on a PVC; the Connect server is disposable.

```bash
k -n spark delete pod -l app=spark-connect     # kill it mid-demo
k -n spark rollout status deploy/spark-connect # ~30s to replace
# show the catalog survived:
k -n airflow exec deploy/airflow-dag-processor -c dag-processor -- \
  env SPARK_REMOTE=sc://spark-connect.spark.svc.cluster.local:15002 \
  python -c "from pyspark.sql import SparkSession; \
  print(SparkSession.builder.getOrCreate().sql('SHOW DATABASES').show())"
# then trigger any pipeline — business as usual
```

## 7. Access story

```bash
# add a user to USERS in scripts/create-users.sh, then:
make users     # 32-char token printed once
# revoke:
k -n airflow exec deploy/airflow-api-server -- airflow users delete --username <name>
```

---

## Reset between demos

```bash
# clear demo tables (medallion db is recreated by the imperative DAG)
k -n airflow exec deploy/airflow-dag-processor -c dag-processor -- \
  env SPARK_REMOTE=sc://spark-connect.spark.svc.cluster.local:15002 \
  python -c "from pyspark.sql import SparkSession; \
  SparkSession.builder.getOrCreate().sql('DROP DATABASE IF EXISTS medallion CASCADE')"
# delete stray incoming/ files
aws s3 rm s3://sdp-pipeline-storage-68729b89/incoming/ --recursive
```
