# CineMetrics — Architecture (technical detail)

Companion to the [README](../README.md). Focuses on the engineering decisions behind the "As-Built" implementation.

## End-to-end data flow

1. **Batch** — `ingest_movies.py` downloads MovieLens (movies, ratings, tags, links) and writes the raw files to **BRONZE** (MinIO). If `TMDB_API_KEY` is set, it enriches the data with the TMDb API.
2. **Streaming** — `event_producer.py` publishes player events (play/pause/stop/seek/complete) to the Kafka topic `streaming_events`. The `stream_events_to_bronze.py` job (Spark Structured Streaming) consumes them and writes Delta to **BRONZE**, with a 5-minute windowed aggregate in **SILVER**.
3. **Medallion (Spark)** — `bronze_to_silver.py` cleans/casts/deduplicates → **SILVER** (Delta). `silver_to_gold.py` computes the aggregates → **GOLD** (Delta) and publishes them to Postgres (serving).
4. **Marts/Quality (dbt)** — `genre_kpis` (view) + 11 tests (`not_null`, `unique`) on the gold layer.
5. **Serving** — Metabase (dashboard) and FastAPI read the gold layer from Postgres.
6. **Orchestration** — Airflow chains 1→3→4 (DAG `cinemetrics_pipeline`, `@daily`).
7. **Observability** — Prometheus (postgres-exporter) + Grafana.

## Why Lakehouse + Medallion

Delta Lake on MinIO (S3) provides **ACID transactions, time travel and schema enforcement** on cheap object storage, combining batch and streaming in the same storage layer. The medallion pattern separates responsibilities: bronze (raw/auditable), silver (trusted), gold (consumable).

## Key technical decisions

- **Spark 3.5.3 (Scala 2.12, Hadoop 3.3.4, JDK 11):** version aligned with Delta 3.2.1 and the `hadoop-aws` 3.3.4 connector (s3a). Jars are downloaded at build time (offline at runtime).
- **S3 credentials from the environment:** `EnvironmentVariableCredentialsProvider` (no secrets baked into the image).
- **Kafka in KRaft mode:** no ZooKeeper, one less container and less RAM.
- **Gold in Delta *and* Postgres:** Delta = analytical/auditable layer; Postgres = low-latency serving for BI/API.
- **Airflow via `docker exec`:** the container has the Docker CLI + the mounted socket; tasks run inside the ingestion/Spark containers (no need to repackage dependencies into Airflow).
- **Compose profiles:** `core` always on; `streaming`, `orchestration`, `serving`, `api`, `monitoring` on demand, so it fits in 16 GB by starting only what is needed.

## Retention policies (governance)

| Layer | Retention |
|---|---|
| BRONZE | 90 days (raw) |
| SILVER | 2 years |
| GOLD | indefinite |

## Known limitations (prototype)

- Spark runs in local mode (`local[*]`), not on a cluster, which is enough for the MovieLens volume.
- The 5-minute streaming window only materializes in silver after the window closes + the watermark.
- Spark/Kafka metrics in Prometheus would require additional exporters (out of scope for the prototype).
