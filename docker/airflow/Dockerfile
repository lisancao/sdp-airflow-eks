# Airflow image with the Spark Connect client stack for running
# Spark Declarative Pipelines from Airflow tasks.
FROM apache/airflow:3.1.8-python3.12

# pyspark[connect] brings grpcio, pyarrow, and a pandas version that
# satisfies pyspark 4.1's floor (plain `pyspark` does not).
# Provider >= 6.2.0 ships the official SparkPipelinesOperator with native
# Spark Connect support; the vendored copy in dags/ is only a fallback.
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark==6.2.0 \
    'pyspark[connect]==4.1.0'
