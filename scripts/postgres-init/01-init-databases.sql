-- Postgres initialization (runs once on first startup, empty volume).
-- Creates the auxiliary databases and the GOLD layer schema.

CREATE DATABASE airflow;    -- Airflow metadata (orchestration)
CREATE DATABASE metabase;   -- Metabase app database (serving/BI)

\connect cinemetrics
CREATE SCHEMA IF NOT EXISTS gold;
COMMENT ON SCHEMA gold IS 'GOLD layer served to Metabase (business aggregates).';
