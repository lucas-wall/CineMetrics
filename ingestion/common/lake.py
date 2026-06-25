"""Helpers de acesso ao Data Lake (MinIO / S3) via boto3."""
import os
import boto3
from botocore.client import Config


def s3_client():
    """Cliente S3 apontando para o MinIO (path-style, credenciais do ambiente)."""
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT", "http://minio:9000"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def put_bytes(client, bucket, key, data: bytes, content_type="application/octet-stream"):
    client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)


def put_file(client, bucket, key, path):
    client.upload_file(path, bucket, key)
