from pathlib import Path
from typing import List, Union

from .base import StorageDriver


class LocalDriver(StorageDriver):

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path: str) -> Path:
        full = (self.root / path).resolve()
        if not str(full).startswith(str(self.root) + '/') and full != self.root:
            raise ValueError(f"Path traversal attempt blocked: {path!r}")
        return full

    def put(self, path: str, content: Union[bytes, str], **kwargs) -> bool:
        full = self._safe_path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        mode = 'wb' if isinstance(content, bytes) else 'w'
        with open(full, mode) as fh:
            fh.write(content)
        return True

    def get(self, path: str) -> bytes:
        with open(self._safe_path(path), 'rb') as fh:
            return fh.read()

    def delete(self, path: str) -> bool:
        target = self._safe_path(path)
        if target.exists():
            target.unlink()
            return True
        return False

    def exists(self, path: str) -> bool:
        return self._safe_path(path).exists()

    def url(self, path: str) -> str:
        return f"/storage/{path}"

    def list(self, prefix: str = '') -> List[str]:
        search_root = self._safe_path(prefix) if prefix else self.root
        if not search_root.exists():
            return []
        return [
            str(p.relative_to(self.root))
            for p in search_root.rglob('*')
            if p.is_file()
        ]
