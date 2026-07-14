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

# Trigger with config {"spec_path": ".../pipelines/broken/spark-pipeline.yml"}
# to demo the gate: dry-run fails on the broken graph and the run task
# never starts. No config -> the real spec, normal daily behavior.
TEMPLATED_SPEC = (
    "{{ dag_run.conf.get('spec_path', '" + PIPELINE_SPEC + "') }}"
)

with DAG(
    dag_id="sdp_validate_then_run",
    description="Dry-run the pipeline spec, then execute it",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["spark", "sdp"],
):
    validate = SparkPipelinesOperator(
        task_id="validate",
        pipeline_spec=TEMPLATED_SPEC,
        pipeline_command="dry-run",
    )

    # Note: the provider operator (>= 6.2.0) does not expose the CLI's
    # --full-refresh flags yet, so this is a default incremental run.
    run = SparkPipelinesOperator(
        task_id="run",
        pipeline_spec=TEMPLATED_SPEC,
        pipeline_command="run",
    )

    validate >> run
