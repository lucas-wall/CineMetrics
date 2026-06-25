"""
Ingestão BATCH do catálogo CineMetrics → camada BRONZE (raw).

Fonte primária: MovieLens (GroupLens) — filmes + ratings + tags + links REAIS.
Se TMDB_API_KEY estiver definido no .env, enriquece uma amostra com metadados
oficiais do TMDb (mantendo o espírito "TMDb real" do plano da Parte 1).

A camada BRONZE preserva o formato original dos dados (CSV/JSON), sem
transformação — conforme a arquitetura Medalhão.
"""
import os
import sys
import json
import zipfile
import urllib.request
import datetime as dt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../ingestion
from common.lake import s3_client, put_bytes, put_file

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/{ds}.zip"
BRONZE = os.getenv("BRONZE_BUCKET", "bronze")
DATASET = os.getenv("MOVIELENS_DATASET", "ml-latest-small")
TMDB_KEY = os.getenv("TMDB_API_KEY", "").strip()


def log(msg):
    print(f"[ingest-batch] {msg}", flush=True)


def download_movielens(dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    url = MOVIELENS_URL.format(ds=DATASET)
    zpath = os.path.join(dest_dir, f"{DATASET}.zip")
    if not os.path.exists(zpath):
        log(f"baixando dataset real: {url}")
        urllib.request.urlretrieve(url, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(dest_dir)
    return os.path.join(dest_dir, DATASET)


def enrich_tmdb(client, base, sample=50):
    """Enriquecimento opcional com a API do TMDb (se houver key)."""
    import csv
    links = os.path.join(base, "links.csv")
    out = []
    with open(links, encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            if i >= sample:
                break
            tmdb_id = (row.get("tmdbId") or "").strip()
            if not tmdb_id:
                continue
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_KEY}"
            try:
                with urllib.request.urlopen(url, timeout=10) as r:
                    out.append(json.loads(r.read()))
            except Exception as e:  # noqa: BLE001
                log(f"tmdb {tmdb_id} falhou: {e}")
    put_bytes(client, BRONZE, "tmdb/movies_enriched.json",
              json.dumps(out).encode(), "application/json")
    log(f"TMDb: {len(out)} filmes enriquecidos -> s3://{BRONZE}/tmdb/")


def main():
    client = s3_client()
    base = download_movielens("/app/data/movielens")
    files = ["movies.csv", "ratings.csv", "tags.csv", "links.csv"]
    counts = {}
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for f in files:
        path = os.path.join(base, f)
        if not os.path.exists(path):
            log(f"AVISO: {f} ausente no dataset")
            continue
        name = f[:-4]
        key = f"movielens/{name}/{f}"
        put_file(client, BRONZE, key, path)
        with open(path, encoding="utf-8") as fh:
            n = sum(1 for _ in fh) - 1  # menos o header
        counts[name] = n
        log(f"-> s3://{BRONZE}/{key}  ({n} linhas)")

    source = "movielens"
    if TMDB_KEY:
        source = "movielens+tmdb"
        enrich_tmdb(client, base)
    else:
        log("TMDB_API_KEY vazio -> fonte = MovieLens (real). Fallback documentado no As-Built.")

    manifest = {"source": source, "dataset": DATASET,
                "ingested_at": ts, "row_counts": counts}
    put_bytes(client, BRONZE, "movielens/_manifest.json",
              json.dumps(manifest, indent=2).encode(), "application/json")
    log(f"manifesto -> s3://{BRONZE}/movielens/_manifest.json  {manifest}")
    log("ingestão BATCH concluída ✅")


if __name__ == "__main__":
    main()
