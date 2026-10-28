# Airflow with the Docker CLI, to orchestrate tasks via `docker exec`
# in the ingestion and Spark containers (BashOperator).
FROM apache/airflow:2.10.5

USER root
# Docker CLI (talks to the host's mounted socket) — client only, no daemon.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow
