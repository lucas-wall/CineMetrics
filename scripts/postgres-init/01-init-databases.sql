-- Inicialização do Postgres (roda 1x na primeira subida, volume vazio).
-- Cria os bancos auxiliares e o schema da camada GOLD.

CREATE DATABASE airflow;    -- metadados do Airflow (orquestração)
CREATE DATABASE metabase;   -- app database do Metabase (serving/BI)

\connect cinemetrics
CREATE SCHEMA IF NOT EXISTS gold;
COMMENT ON SCHEMA gold IS 'Camada GOLD servida ao Metabase (agregados de negócio).';
