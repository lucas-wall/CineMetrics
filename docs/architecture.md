# CineMetrics — Arquitetura (detalhe técnico)

Complemento ao [README](../README.md). Foca nas decisões de engenharia que sustentam o "As-Built".

## Fluxo de dados ponta a ponta

1. **Batch** — `ingest_movies.py` baixa o MovieLens (filmes, ratings, tags, links), grava o cru no **BRONZE** (MinIO). Se `TMDB_API_KEY` existir, enriquece com a API do TMDb.
2. **Streaming** — `event_producer.py` publica eventos de player (play/pause/stop/seek/complete) no tópico Kafka `streaming_events`. O job `stream_events_to_bronze.py` (Spark Structured Streaming) consome e grava em Delta no **BRONZE**, com agregação em janela de 5 min no **SILVER**.
3. **Medalhão (Spark)** — `bronze_to_silver.py` limpa/tipa/deduplica → **SILVER** (Delta). `silver_to_gold.py` calcula os agregados → **GOLD** (Delta) e publica no Postgres (serving).
4. **Marts/Qualidade (dbt)** — `genre_kpis` (view) + 11 testes (`not_null`, `unique`) sobre o gold.
5. **Serving** — Metabase (dashboard) e FastAPI leem o gold no Postgres.
6. **Orquestração** — Airflow encadeia 1→3→4 (DAG `cinemetrics_pipeline`, `@daily`).
7. **Observabilidade** — Prometheus (postgres-exporter) + Grafana.

## Por que Lakehouse + Medalhão

Delta Lake sobre MinIO (S3) dá **ACID, time travel e schema enforcement** sobre object storage barato — combina batch e streaming no mesmo armazenamento. O medalhão separa responsabilidades: bronze (raw/auditável), silver (confiável), gold (consumível).

## Decisões técnicas relevantes

- **Spark 3.5.3 (Scala 2.12, Hadoop 3.3.4, JDK 11):** versão alinhada a Delta 3.2.1 e ao conector `hadoop-aws` 3.3.4 (s3a). Jars baixados em build-time (offline em runtime).
- **Credenciais S3 por ambiente:** `EnvironmentVariableCredentialsProvider` (sem segredo na imagem).
- **Kafka em modo KRaft:** sem ZooKeeper — um container a menos, menos RAM.
- **gold em Delta *e* Postgres:** Delta = camada analítica/auditável; Postgres = serving de baixa latência p/ BI/API.
- **Airflow via `docker exec`:** o container tem o CLI do Docker + o socket montado; as tasks rodam nos containers de ingestão/Spark (sem reempacotar dependências no Airflow).
- **Perfis Compose:** `core` sempre; `streaming`, `orchestration`, `serving`, `api`, `monitoring` sob demanda — cabe em 16 GB subindo só o necessário.

## Políticas de retenção (governança)

| Camada | Retenção |
|---|---|
| BRONZE | 90 dias (raw) |
| SILVER | 2 anos |
| GOLD | indefinido |

## Limitações conhecidas (protótipo)

- Spark roda em modo local (`local[*]`), não em cluster — suficiente p/ o volume do MovieLens.
- A janela de 5 min do streaming só materializa no silver após o fechamento da janela + watermark.
- Métricas de Spark/Kafka no Prometheus exigiriam exporters adicionais (fora do escopo do protótipo).
