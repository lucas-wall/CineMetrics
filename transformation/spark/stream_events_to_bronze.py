"""
STREAMING: Kafka 'streaming_events' -> BRONZE (raw) + SILVER (janela 5 min).

Spark Structured Streaming consome os eventos do player publicados no Kafka,
grava o cru em Delta no BRONZE e mantém um agregado em janela de 5 min no SILVER
(plays por filme), demonstrando o caminho de tempo real do pipeline.

Submetido com o pacote spark-sql-kafka (resolvido via --packages no compose).
"""
import os
from pyspark.sql import SparkSession, functions as F, types as T

KAFKA = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC_EVENTS", "streaming_events")
BRONZE = "s3a://bronze"
SILVER = "s3a://silver"
CKPT = "s3a://warehouse/checkpoints"

EVENT_SCHEMA = T.StructType([
    T.StructField("event_id", T.StringType()),
    T.StructField("user_id", T.StringType()),
    T.StructField("movie_id", T.LongType()),
    T.StructField("event_type", T.StringType()),
    T.StructField("timestamp", T.StringType()),
    T.StructField("device", T.StringType()),
    T.StructField("playback_position_seconds", T.LongType()),
    T.StructField("video_quality", T.StringType()),
])


def main():
    spark = SparkSession.builder.appName("stream_events_to_bronze").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    events = (
        raw.select(F.from_json(F.col("value").cast("string"), EVENT_SCHEMA).alias("e"))
        .select("e.*")
        .withColumn("event_time", F.to_timestamp("timestamp"))
        .withColumn("ingest_date", F.current_date())
    )

    # BRONZE: eventos crus (append contínuo)
    q_bronze = (
        events.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CKPT}/events_bronze")
        .partitionBy("ingest_date")
        .start(f"{BRONZE}/streaming_events")
    )

    # SILVER: janela de 5 min — plays por filme (watermark p/ estado limitado)
    windowed = (
        events.filter(F.col("event_type") == "play")
        .withWatermark("event_time", "10 minutes")
        .groupBy(F.window("event_time", "5 minutes"), F.col("movie_id"))
        .agg(F.count("*").alias("plays"))
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "movie_id", "plays",
        )
    )
    q_silver = (
        windowed.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CKPT}/events_windowed")
        .start(f"{SILVER}/events_windowed")
    )

    print(f"[streaming] consumindo {TOPIC}@{KAFKA} -> bronze/streaming_events + silver/events_windowed", flush=True)
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
