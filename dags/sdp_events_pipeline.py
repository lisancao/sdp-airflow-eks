"""Run the events declarative pipeline on a schedule.

The task attaches to the Spark Connect server (SPARK_REMOTE) and executes
the pipeline described by pipelines/spark-pipeline.yml. The dataflow graph
lives in the spec, not the DAG — Airflow decides *when*, SDP decides *what*.
"""

from datetime import datetime

from airflow.sdk import DAG

try:
    from airflow.providers.apache.spark.operators.spark_pipelines import (
        SparkPipelinesOperator,
    )
except ImportError:
    from spark_pipelines_operator import SparkPipelinesOperator

PIPELINE_SPEC = "/opt/airflow/dags/repo/pipelines/spark-pipeline.yml"

with DAG(
    dag_id="sdp_events_pipeline",
    description="Hourly incremental run of the events declarative pipeline",
    schedule="@hourly",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["spark", "sdp"],
):
    SparkPipelinesOperator(
        task_id="run_pipeline",
        pipeline_spec=PIPELINE_SPEC,
        pipeline_command="run",
    )
