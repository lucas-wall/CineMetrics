-- KPIs by genre (MARTS layer via dbt, on top of the GOLD layer materialized by Spark).
-- Demonstrates a versioned + tested transformation in the lifecycle.
select
    genre,
    total_ratings,
    avg_rating,
    n_movies,
    round(total_ratings::numeric / nullif(n_movies, 0), 1) as ratings_por_filme
from {{ source('gold', 'genre_popularity') }}
order by total_ratings desc
