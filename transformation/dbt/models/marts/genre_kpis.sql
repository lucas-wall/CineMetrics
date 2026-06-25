-- KPIs por gênero (camada de MARTS via dbt, sobre o GOLD materializado pelo Spark).
-- Demonstra transformação versionada + testada no ciclo de vida.
select
    genre,
    total_ratings,
    avg_rating,
    n_movies,
    round(total_ratings::numeric / nullif(n_movies, 0), 1) as ratings_por_filme
from {{ source('gold', 'genre_popularity') }}
order by total_ratings desc
