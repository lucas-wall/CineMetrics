"""
BRONZE -> SILVER (batch).

Lê os CSVs crus do catálogo (MovieLens) na camada BRONZE (S3A/MinIO),
limpa/tipa/deduplica e grava tabelas Delta na camada SILVER.

SILVER = dados limpos, conformados, com schema enforcement (Delta).
"""
from pyspark.sql import SparkSession, functions as F

BRONZE = "s3a://bronze"
SILVER = "s3a://silver"


def main():
    spark = (SparkSession.builder.appName("bronze_to_silver").getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    # ---------- MOVIES (catálogo) ----------
    movies = (
        spark.read.option("header", True).csv(f"{BRONZE}/movielens/movies/movies.csv")
        .withColumn("movieId", F.col("movieId").cast("int"))
        .withColumn("year", F.regexp_extract("title", r"\((\d{4})\)", 1))
        .withColumn("year", F.when(F.col("year") == "", None).otherwise(F.col("year").cast("int")))
        .withColumn("title_clean", F.trim(F.regexp_replace("title", r"\s*\(\d{4}\)\s*$", "")))
        .withColumn("genres_arr", F.split("genres", r"\|"))
        .filter(F.col("movieId").isNotNull())
        .dropDuplicates(["movieId"])
    )
    movies.write.format("delta").mode("overwrite").save(f"{SILVER}/movies")

    # ---------- RATINGS (interações reais) ----------
    ratings = (
        spark.read.option("header", True).csv(f"{BRONZE}/movielens/ratings/ratings.csv")
        .withColumn("userId", F.col("userId").cast("int"))
        .withColumn("movieId", F.col("movieId").cast("int"))
        .withColumn("rating", F.col("rating").cast("double"))
        .withColumn("event_time", F.to_timestamp(F.from_unixtime(F.col("timestamp").cast("long"))))
        .filter("rating is not null and movieId is not null and userId is not null")
        .dropDuplicates(["userId", "movieId", "timestamp"])
    )
    ratings.write.format("delta").mode("overwrite").save(f"{SILVER}/ratings")

    # ---------- LINKS (movieId -> imdb/tmdb) ----------
    links = (
        spark.read.option("header", True).csv(f"{BRONZE}/movielens/links/links.csv")
        .withColumn("movieId", F.col("movieId").cast("int"))
        .filter(F.col("movieId").isNotNull())
    )
    links.write.format("delta").mode("overwrite").save(f"{SILVER}/links")

    # ---------- USERS (derivados dos ratings) ----------
    users = (
        ratings.groupBy("userId").agg(
            F.count("*").alias("n_ratings"),
            F.min("event_time").alias("first_seen"),
            F.max("event_time").alias("last_seen"),
            F.round(F.avg("rating"), 3).alias("avg_rating"),
        )
    )
    users.write.format("delta").mode("overwrite").save(f"{SILVER}/users")

    for t in ["movies", "ratings", "links", "users"]:
        c = spark.read.format("delta").load(f"{SILVER}/{t}").count()
        print(f"[silver] {t}: {c} linhas", flush=True)
    print("BRONZE->SILVER ok ✅", flush=True)
    spark.stop()


if __name__ == "__main__":
    main()
