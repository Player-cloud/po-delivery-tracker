"""
The `Storage` interface for attachment blobs (M3).

The attachment CRUD only ever talks to this abstract class, so the same code
path runs in every environment (mirrors the `NotificationSender` pattern):

- local dev  -> `LocalStorage` under `settings.local_upload_dir`
- production -> `S3Storage` against Cloudflare R2

Pick one with `app.services.storage.get_storage()`, which reads
`settings.storage_backend`.

A `key` is an opaque forward-slash path the CRUD generates
(`po_lines/<id>/<uuid>_<name>`); the backend maps it to a file or an object.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageError(Exception):
    """Raised when a blob can't be written, read, or removed."""


class Storage(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str | None = None) -> None: ...

    @abstractmethod
    def load(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the blob. Must not raise if the key is already gone."""
