"""Factory: turn `settings.storage_backend` into a concrete Storage."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.base import Storage, StorageError

__all__ = ["Storage", "StorageError", "get_storage"]


@lru_cache
def get_storage() -> Storage:
    backend = get_settings().storage_backend.lower()

    if backend == "local":
        from app.services.storage.local import LocalStorage

        return LocalStorage()
    if backend == "s3":
        from app.services.storage.s3 import S3Storage

        return S3Storage()

    raise StorageError(f"Unknown STORAGE_BACKEND {backend!r} — expected: local, s3")
