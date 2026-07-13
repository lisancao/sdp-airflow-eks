"""Validate the pipeline graph before executing it.

`dry-run` builds and checks the dataflow graph without processing data,
so a broken spec or transformation fails fast in a cheap task instead of
mid-run. Useful as a deploy gate: git-sync pulls new pipeline code, the
next scheduled run validates it before touching tables.
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
    dag_id="sdp_validate_then_run",
    description="Dry-run the pipeline spec, then execute a full refresh",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["spark", "sdp"],
):
    validate = SparkPipelinesOperator(
        task_id="validate",
        pipeline_spec=PIPELINE_SPEC,
        pipeline_command="dry-run",
    )

    run = SparkPipelinesOperator(
        task_id="run",
        pipeline_spec=PIPELINE_SPEC,
        pipeline_command="run",
        full_refresh=True,
    )

    validate >> run
