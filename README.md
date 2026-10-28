# 🎬 CineMetrics: End-to-End Streaming Data Lakehouse

CineMetrics is a laptop-sized data platform for a movie streaming service. It ingests real MovieLens ratings and simulated player events, refines them through a Delta Lake medallion (bronze, silver, gold), tests the results with dbt, and serves them through a BI dashboard and a REST API.

## Stack

`Python` · `Apache Kafka` (KRaft) · `MinIO` (S3) · `Delta Lake` · `Apache Spark 3.5.3` (PySpark + Structured Streaming) · `dbt` (Postgres) · `PostgreSQL` · `Apache Airflow` · `Metabase` · `FastAPI` · `Prometheus` · `Grafana` · `Docker Compose`

## What it does

- Batch-ingests the MovieLens dataset (movies, ratings, tags, links) into the bronze layer on MinIO, with optional TMDb enrichment when `TMDB_API_KEY` is set.
- Streams synthetic player events (play, pause, seek, complete, buffer) through Kafka into bronze with Spark Structured Streaming, plus a 5-minute windowed plays-per-movie aggregate in silver.
- Cleans, casts and deduplicates data into silver Delta tables, then builds gold aggregates (`movie_metrics`, `genre_popularity`, `ratings_over_time`, `top_movies`) and publishes them to Postgres.
- Runs a dbt mart (`genre_kpis`) with `not_null` / `unique` tests as a data quality gate.
- Orchestrates ingestion, medallion jobs and dbt in a daily Airflow DAG (`cinemetrics_pipeline`).
- Serves gold data through Metabase and FastAPI (`/genres`, `/top-movies`, `/activity`), with Postgres monitored by Prometheus + Grafana.

## How to run

Requires Docker + Docker Compose (tested on Apple Silicon with 16 GB RAM).

```bash
cp .env.example .env

# Storage, Spark and ingestion containers (creates the medallion buckets)
docker compose up -d                      # or: make up

# Batch pipeline: ingest -> silver -> gold
make pipeline

# Optional profiles
docker compose --profile orchestration up -d airflow   # Airflow   http://localhost:8080 (admin/admin)
docker compose --profile serving up -d metabase        # Metabase  http://localhost:3000
docker compose --profile api up -d api                 # FastAPI   http://localhost:8000/docs
docker compose --profile streaming up -d               # Kafka + producer + Spark Streaming
docker compose --profile monitoring up -d              # Prometheus :9090 / Grafana :3001

make down    # stop everything (keeps volumes)
```

Open [`demo/index.html`](demo/index.html) for a single page with links to every service. Architecture details: [`docs/architecture.md`](docs/architecture.md); original design plan: [`docs/part1-plan.md`](docs/part1-plan.md).

## Credits

Group project originally by [jamillerochagh](https://github.com/jamillerochagh) ([jamillerochagh/CineMetrics](https://github.com/jamillerochagh/CineMetrics)), with Lucas Wall as contributor.
