"""
CineMetrics API (FastAPI) — serving da camada GOLD.

Expõe os agregados de negócio prontos (camada gold no Postgres) via REST,
demonstrando o consumo programático do pipeline (além do BI no Metabase).
"""
import os
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="CineMetrics API",
    description="Serving da camada gold do pipeline CineMetrics.",
    version="1.0.0",
)


def _conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "cinemetrics"),
        user=os.getenv("POSTGRES_USER", "cinemetrics"),
        password=os.getenv("POSTGRES_PASSWORD", "cinemetrics"),
    )


def query(sql, args=None):
    with _conn() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, args or ())
        return cur.fetchall()


@app.get("/health")
def health():
    try:
        query("SELECT 1")
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/genres")
def genres():
    """Popularidade por gênero (gold.genre_popularity)."""
    return query(
        "SELECT genre, total_ratings, avg_rating, n_movies "
        "FROM gold.genre_popularity ORDER BY total_ratings DESC"
    )


@app.get("/top-movies")
def top_movies(limit: int = 10):
    """Top filmes por popularidade (gold.movie_metrics)."""
    return query(
        "SELECT title_clean, n_ratings, avg_rating, unique_viewers "
        "FROM gold.movie_metrics ORDER BY n_ratings DESC LIMIT %s",
        (limit,),
    )


@app.get("/activity")
def activity():
    """Atividade mensal (gold.ratings_over_time)."""
    return query(
        "SELECT month, n_ratings, active_users "
        "FROM gold.ratings_over_time ORDER BY month"
    )
