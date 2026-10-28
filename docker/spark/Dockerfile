# Spark + Delta Lake + S3A (MinIO) + Postgres JDBC image, pinned to Spark 3.5.3.
# Jars downloaded at build time (offline at runtime), matched with:
#   Spark 3.5.3 / Scala 2.12 / Hadoop 3.3.4
FROM apache/spark:3.5.3

USER root

# Delta Lake + S3A connector + Postgres JDBC driver (gold serving).
RUN set -eux; cd /opt/spark/jars; python3 - <<'PY'
import urllib.request
M = "https://repo1.maven.org/maven2"
jars = [
    f"{M}/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar",
    f"{M}/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar",
    f"{M}/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar",
    f"{M}/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar",
    f"{M}/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar",
]
for u in jars:
    fn = u.rsplit("/", 1)[1]
    print("downloading", fn, flush=True)
    urllib.request.urlretrieve(u, fn)
print("jars Delta/S3A/JDBC ok")
PY

COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf

USER spark
WORKDIR /opt/spark
