"""Events pipeline: synthetic bronze ingest -> cleaned silver -> gold rollup.

The runtime infers dataset dependencies from `spark.table(...)` reads and
orders the flows accordingly — nothing is wired explicitly. Replace
`raw_events` with a real source (Kafka, file ingest, JDBC) once the
plumbing is proven end to end.
"""

from pyspark import pipelines as dp
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

spark = SparkSession.active()


@dp.materialized_view(comment="Synthetic raw events, regenerated each run")
def raw_events() -> DataFrame:
    return (
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
            F.current_timestamp() - F.make_interval(secs=F.col("id").cast("double")),
        )
    )


@dp.materialized_view(comment="Events with obvious junk removed")
def clean_events() -> DataFrame:
    events = spark.table("raw_events")
    return events.where(F.col("amount") > 0).where(F.col("event_type").isNotNull())


@dp.materialized_view(comment="Revenue and volume by event type")
def events_summary() -> DataFrame:
    return (
        spark.table("clean_events")
        .groupBy("event_type")
        .agg(
            F.count("*").alias("event_count"),
            F.round(F.sum("amount"), 2).alias("total_amount"),
        )
    )
