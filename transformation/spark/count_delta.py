"""Utility: counts rows of Delta tables (pass s3a:// paths as args)."""
import sys
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("count_delta").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
for p in sys.argv[1:]:
    try:
        df = spark.read.format("delta").load(p)
        print(f"{p} -> {df.count()} rows | columns: {', '.join(df.columns)}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"{p} -> ERROR: {str(e)[:160]}", flush=True)
spark.stop()
