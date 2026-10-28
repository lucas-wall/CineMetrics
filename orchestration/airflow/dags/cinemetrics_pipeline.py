"""
CineMetrics DAG — orchestration of the batch (medallion) pipeline.

Chains: ingestion (MovieLens -> bronze) -> bronze->silver -> silver->gold
-> data quality tests (dbt). Tasks run via `docker exec` in the
ingestion/Spark containers (Airflow has the Docker CLI + the mounted socket).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "data-eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="cinemetrics_pipeline",
    description="CineMetrics lifecycle: ingestion -> medallion -> quality",
    schedule="@daily",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    default_args=default_args,
    tags=["cinemetrics", "data-engineering"],
) as dag:

    start = EmptyOperator(task_id="start")

    ingest_batch = BashOperator(
        task_id="ingest_batch_movielens",
        bash_command="docker exec cinemetrics-ingestion python ingestion/batch/ingest_movies.py",
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command="docker exec cinemetrics-spark /opt/spark/bin/spark-submit /opt/jobs/bronze_to_silver.py",
    )

    silver_to_gold = BashOperator(
        task_id="silver_to_gold",
        bash_command="docker exec cinemetrics-spark /opt/spark/bin/spark-submit /opt/jobs/silver_to_gold.py",
    )

    data_quality = BashOperator(
        task_id="data_quality_dbt",
        bash_command=(
            "docker exec cinemetrics-ingestion "
            "dbt build --project-dir /app/dbt --profiles-dir /app/dbt"
        ),
    )

    end = EmptyOperator(task_id="end")

    start >> ingest_batch >> bronze_to_silver >> silver_to_gold >> data_quality >> end
