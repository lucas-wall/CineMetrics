"""Utilitário: conta linhas de tabelas Delta (passar paths s3a:// como args)."""
import sys
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("count_delta").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
for p in sys.argv[1:]:
    try:
        df = spark.read.format("delta").load(p)
        print(f"{p} -> {df.count()} linhas | colunas: {', '.join(df.columns)}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"{p} -> ERRO: {str(e)[:160]}", flush=True)
spark.stop()
