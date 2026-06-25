# CineMetrics — atalhos de operação
COMPOSE = docker compose
ALL_PROFILES = --profile orchestration --profile serving --profile api --profile streaming --profile monitoring

.PHONY: up pipeline orchestration serving stream monitoring all down ps clean help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## storage + processamento + ingestao (+ cria buckets)
	$(COMPOSE) up -d

pipeline: ## roda o pipeline batch (ingest -> silver -> gold)
	docker exec cinemetrics-ingestion python ingestion/batch/ingest_movies.py
	docker exec cinemetrics-spark /opt/spark/bin/spark-submit /opt/jobs/bronze_to_silver.py
	docker exec cinemetrics-spark /opt/spark/bin/spark-submit /opt/jobs/silver_to_gold.py

orchestration: ## sobe o Airflow (http://localhost:8080)
	$(COMPOSE) --profile orchestration up -d

serving: ## sobe Metabase (:3000) + FastAPI (:8000)
	$(COMPOSE) --profile serving up -d
	$(COMPOSE) --profile api up -d

stream: ## sobe Kafka + producer + Spark Streaming
	$(COMPOSE) --profile streaming up -d

monitoring: ## sobe Prometheus (:9090) + Grafana (:3001)
	$(COMPOSE) --profile monitoring up -d

all: up orchestration serving stream monitoring ## sobe a stack inteira

ps: ## status dos containers
	$(COMPOSE) $(ALL_PROFILES) ps

down: ## derruba tudo (mantem volumes)
	$(COMPOSE) $(ALL_PROFILES) down

clean: ## derruba tudo + volumes (reset total)
	$(COMPOSE) $(ALL_PROFILES) down -v
