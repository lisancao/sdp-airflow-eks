"""Event-driven pipeline: a file landing in S3 triggers the SDP run.

Demo:
  1. Trigger this DAG — the sensor starts polling s3://<bucket>/incoming/
  2. Drop a file:  aws s3 cp anything.json s3://<bucket>/incoming/demo.json
  3. Within ~30s the sensor goes green and the pipeline runs
  4. The cleanup task removes the marker so the demo is repeatable

The sensor task pod authenticates to S3 via IRSA (no AWS connection
configured — boto3 falls through to the injected web-identity token).
"""

from datetime import datetime, timedelta

from airflow.sdk import DAG, task
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

try:
    from airflow.providers.apache.spark.operators.spark_pipelines import (
        SparkPipelinesOperator,
    )
except ImportError:
    from spark_pipelines_operator import SparkPipelinesOperator

BUCKET = "sdp-pipeline-storage-68729b89"
INCOMING = "incoming/*.json"
PIPELINE_SPEC = "/opt/airflow/dags/repo/pipelines/spark-pipeline.yml"

with DAG(
    dag_id="s3_event_pipeline",
    description="Run the events pipeline when a file lands in S3",
    schedule=None,
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["spark", "sdp", "event-driven"],
):
    wait_for_file = S3KeySensor(
        task_id="wait_for_file",
        bucket_name=BUCKET,
        bucket_key=INCOMING,
        wildcard_match=True,
        mode="reschedule",
        poke_interval=timedelta(seconds=30),
        timeout=timedelta(hours=2),
    )

    run_pipeline = SparkPipelinesOperator(
        task_id="run_pipeline",
        pipeline_spec=PIPELINE_SPEC,
        pipeline_command="run",
    )

    @task
    def clear_marker():
        import boto3

        s3 = boto3.client("s3")
        listed = s3.list_objects_v2(Bucket=BUCKET, Prefix="incoming/")
        for obj in listed.get("Contents", []):
            s3.delete_object(Bucket=BUCKET, Key=obj["Key"])

    wait_for_file >> run_pipeline >> clear_marker()
