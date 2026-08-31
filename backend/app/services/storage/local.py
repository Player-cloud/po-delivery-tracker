"""Local-disk storage — dev default. Files live under `settings.local_upload_dir`."""
from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.services.storage.base import Storage, StorageError

settings = get_settings()


class LocalStorage(Storage):
    def __init__(self, root: str | Path | None = None) -> None:
        self._root = Path(root or settings.local_upload_dir).resolve()

    def _path(self, key: str) -> Path:
        # Defend against traversal: the resolved path must stay under the root.
        target = (self._root / key).resolve()
        if self._root not in target.parents and target != self._root:
            raise StorageError(f"key {key!r} escapes the storage root")
        return target

    def save(self, key: str, data: bytes, content_type: str | None = None) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def load(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise StorageError(f"blob {key!r} not found") from exc

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
