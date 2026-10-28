# Lightweight ingestion image: batch connectors (TMDb/MovieLens) and Kafka producer.
# Build context = repo root (needs requirements.txt + ingestion/).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion ./ingestion

# Container stays alive; tasks are triggered by Airflow (docker exec) or make.
CMD ["python", "-c", "print('cinemetrics ingestion image ready')"]
