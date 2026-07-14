"""Imperative medallion pipeline: the same events flow as the SDP pipeline,
written the traditional way.

Compare with sdp_events_pipeline + pipelines/spark-pipeline.yml:

  Imperative (this file)                Declarative (SDP)
  ----------------------                -----------------
  4 Airflow tasks                       1 Airflow task
  You create the schema                 Spec's `database:` field
  You order the tasks (>>)              Runtime infers order from reads
  You write each table explicitly       Runtime owns persistence
  Retry re-runs a whole task            Runtime tracks per-flow state
  Logic lives in the DAG                DAG only decides *when*

Every task opens its own Spark Connect session, does explicit
read -> transform -> write, and is wired to the next by hand. All the
orchestration knowledge lives here in the DAG file.
"""

import os
from datetime import datetime

from airflow.sdk import DAG, task

DB = "medallion"


def _spark():
    from pyspark.sql import SparkSession

    return SparkSession.builder.remote(os.environ["SPARK_REMOTE"]).getOrCreate()


with DAG(
    dag_id="medallion_imperative",
    description="Bronze -> silver -> gold, hand-wired (imperative style)",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["spark", "imperative", "medallion"],
):

    @task
    def create_schema():
        # Imperative cost #1: schema management is your job.
        spark = _spark()
        try:
            spark.sql(f"CREATE DATABASE IF NOT EXISTS {DB}")
        finally:
            spark.stop()

    @task
    def bronze_ingest():
        # Imperative cost #2: you decide table names, write modes, formats.
        from pyspark.sql import functions as F

        spark = _spark()
        try:
            df = (
                spark.range(0, 10_000)
                .withColumn(
                    "event_type",
                    F.element_at(
                        F.array(F.lit("view"), F.lit("click"), F.lit("purchase")),
                        ((F.col("id") % 3) + 1).cast("int"),
                    ),
                )
                .withColumn("amount", F.round(F.rand() * 100, 2))
                .withColumn(
                    "event_ts",
                    F.current_timestamp()
                    - F.make_interval(secs=F.col("id").cast("double")),
                )
            )
            df.write.mode("overwrite").saveAsTable(f"{DB}.raw_events")
        finally:
            spark.stop()

    @task
    def silver_clean():
        # Imperative cost #3: the dependency on bronze exists only because
        # this task is wired after bronze_ingest below. Nothing checks it.
        from pyspark.sql import functions as F

        spark = _spark()
        try:
            events = spark.table(f"{DB}.raw_events")
            cleaned = events.where(F.col("amount") > 0).where(
                F.col("event_type").isNotNull()
            )
            cleaned.write.mode("overwrite").saveAsTable(f"{DB}.clean_events")
        finally:
            spark.stop()

    @task
    def gold_aggregate():
        from pyspark.sql import functions as F

        spark = _spark()
        try:
            summary = (
                spark.table(f"{DB}.clean_events")
                .groupBy("event_type")
                .agg(
                    F.count("*").alias("event_count"),
                    F.round(F.sum("amount"), 2).alias("total_amount"),
                )
            )
            summary.write.mode("overwrite").saveAsTable(f"{DB}.events_summary")
        finally:
            spark.stop()

    # Imperative cost #4: the graph is maintained by hand. Add a table,
    # remember to rewire this line — the runtime won't notice if you don't.
    create_schema() >> bronze_ingest() >> silver_clean() >> gold_aggregate()
