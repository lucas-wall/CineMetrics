"""
SILVER -> GOLD.

Calcula os agregados de negócio (Delta na camada GOLD) e PUBLICA as tabelas
prontas no Postgres (schema gold) para consumo pelo Metabase.

GOLD = tabelas prontas para BI/ML, agregações pré-calculadas.
"""
import os
from pyspark.sql import SparkSession, functions as F

SILVER = "s3a://silver"
GOLD = "s3a://gold"

PG_URL = os.getenv("PG_JDBC", "jdbc:postgresql://postgres:5432/cinemetrics")
PG_USER = os.getenv("POSTGRES_USER", "cinemetrics")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "cinemetrics")


def to_postgres(df, table):
    """Publica um DataFrame na tabela gold.<table> do Postgres (serving)."""
    (df.write.format("jdbc")
        .option("url", PG_URL)
        .option("dbtable", f"gold.{table}")
        .option("user", PG_USER)
        .option("password", PG_PASS)
        .option("driver", "org.postgresql.Driver")
        .mode("overwrite").save())
    print(f"[gold->postgres] gold.{table} publicado", flush=True)


def main():
    spark = SparkSession.builder.appName("silver_to_gold").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    movies = spark.read.format("delta").load(f"{SILVER}/movies")
    ratings = spark.read.format("delta").load(f"{SILVER}/ratings")

    # ---------- GOLD 1: métricas por filme ----------
    movie_metrics = (
        ratings.groupBy("movieId").agg(
            F.count("*").alias("n_ratings"),
            F.round(F.avg("rating"), 3).alias("avg_rating"),
            F.countDistinct("userId").alias("unique_viewers"),
        )
        .join(movies.select("movieId", "title_clean", "year", "genres_arr"), "movieId", "left")
    )
    movie_metrics.write.format("delta").mode("overwrite").save(f"{GOLD}/movie_metrics")

    # versão "achatada" p/ Postgres (sem arrays)
    movie_metrics_pg = movie_metrics.withColumn(
        "genres", F.concat_ws(", ", "genres_arr")
    ).drop("genres_arr")
    to_postgres(movie_metrics_pg, "movie_metrics")

    # ---------- GOLD 2: popularidade por gênero ----------
    exploded = movie_metrics.withColumn("genre", F.explode("genres_arr"))
    genre_pop = (
        exploded.groupBy("genre").agg(
            F.sum("n_ratings").alias("total_ratings"),
            # média ponderada pelo nº de ratings de cada filme
            F.round(F.sum(F.col("avg_rating") * F.col("n_ratings")) / F.sum("n_ratings"), 3).alias("avg_rating"),
            F.count("*").alias("n_movies"),
        )
        .orderBy(F.desc("total_ratings"))
    )
    genre_pop.write.format("delta").mode("overwrite").save(f"{GOLD}/genre_popularity")
    to_postgres(genre_pop, "genre_popularity")

    # ---------- GOLD 3: atividade ao longo do tempo (mensal) ----------
    ratings_time = (
        ratings.withColumn("month", F.date_format("event_time", "yyyy-MM"))
        .groupBy("month").agg(
            F.count("*").alias("n_ratings"),
            F.countDistinct("userId").alias("active_users"),
        )
        .filter(F.col("month").isNotNull())
        .orderBy("month")
    )
    ratings_time.write.format("delta").mode("overwrite").save(f"{GOLD}/ratings_over_time")
    to_postgres(ratings_time, "ratings_over_time")

    # ---------- GOLD 4: top 20 filmes (popularidade) ----------
    top_movies = (
        movie_metrics_pg.filter(F.col("n_ratings") >= 20)
        .orderBy(F.desc("n_ratings"))
        .limit(20)
    )
    top_movies.write.format("delta").mode("overwrite").save(f"{GOLD}/top_movies")
    to_postgres(top_movies, "top_movies")

    print("SILVER->GOLD ok ✅ (Delta + Postgres)", flush=True)
    spark.stop()


if __name__ == "__main__":
    main()
