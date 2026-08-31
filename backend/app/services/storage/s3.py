"""S3-compatible storage — Cloudflare R2 in production (PRD §13).

R2 speaks the S3 API, so `boto3` works with a custom `endpoint_url` and
region `auto`. Needs `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`,
`S3_SECRET_ACCESS_KEY`.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.services.storage.base import Storage, StorageError

settings = get_settings()


class S3Storage(Storage):
    def __init__(self) -> None:
        try:
            import boto3  # imported lazily so local dev needs no AWS deps
        except ImportError as exc:  # pragma: no cover
            raise StorageError("boto3 is required for STORAGE_BACKEND=s3") from exc

        missing = [
            name
            for name, value in {
                "S3_ENDPOINT_URL": settings.s3_endpoint_url,
                "S3_ACCESS_KEY_ID": settings.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": settings.s3_secret_access_key,
            }.items()
            if not value
        ]
        if missing:
            raise StorageError(f"missing S3 settings: {', '.join(missing)}")

        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )

    def save(self, key: str, data: bytes, content_type: str | None = None) -> None:
        extra = {"ContentType": content_type} if content_type else {}
        try:
            self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)
        except Exception as exc:  # boto3 raises ClientError / BotoCoreError
            raise StorageError(f"S3 put {key!r} failed: {exc}") from exc

    def load(self, key: str) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=key)
            return resp["Body"].read()
        except Exception as exc:
            raise StorageError(f"S3 get {key!r} failed: {exc}") from exc

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:  # pragma: no cover
            raise StorageError(f"S3 delete {key!r} failed: {exc}") from exc
