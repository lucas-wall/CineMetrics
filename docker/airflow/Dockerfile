# Airflow com CLI do Docker, para orquestrar tarefas via `docker exec`
# nos containers de ingestão e Spark (BashOperator).
FROM apache/airflow:2.10.5

USER root
# CLI do Docker (fala com o socket montado do host) — só o cliente, sem daemon.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow
