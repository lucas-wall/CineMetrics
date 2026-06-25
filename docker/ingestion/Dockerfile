# Imagem leve de ingestão: conectores batch (TMDb/MovieLens) e producer Kafka.
# Build context = raiz do repo (precisa de requirements.txt + ingestion/).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion ./ingestion

# Container fica vivo; tarefas são acionadas pelo Airflow (docker exec) ou make.
CMD ["python", "-c", "print('cinemetrics ingestion image pronta')"]
