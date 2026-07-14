"""A transformation with a dependency nothing satisfies.

`upstream_that_nobody_wrote` is not produced by any flow in this
pipeline, so `spark-pipelines dry-run` fails at graph-validation time —
before a single row is read or written.
"""

from pyspark import pipelines as dp
from pyspark.sql import DataFrame, SparkSession

spark = SparkSession.active()


@dp.materialized_view(comment="Depends on a table that does not exist")
def doomed_summary() -> DataFrame:
    return spark.table("upstream_that_nobody_wrote").groupBy("event_type").count()
