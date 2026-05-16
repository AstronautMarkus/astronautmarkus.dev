from typing import Optional

from flask import Flask

from .base import StorageDriver
from .local import LocalDriver
from .s3 import S3Driver


class StorageManager:
    """
    Laravel-style storage manager.

    Resolves the active driver from Flask app config and proxies all
    StorageDriver calls to it.

    Usage:
        storage.put("uploads/photo.jpg", file_bytes)
        storage.get("uploads/photo.jpg")
        storage.exists("uploads/photo.jpg")
        storage.url("uploads/photo.jpg")
        storage.delete("uploads/photo.jpg")
    """

    def __init__(self):
        self._driver: Optional[StorageDriver] = None

    def init_app(self, app: Flask) -> None:
        driver_name = app.config.get('STORAGE_DRIVER', 'local').lower()

        if driver_name == 's3':
            self._driver = S3Driver(
                bucket=app.config['STORAGE_S3_BUCKET'],
                region=app.config['STORAGE_S3_REGION'],
                access_key=app.config['STORAGE_S3_ACCESS_KEY'],
                secret_key=app.config['STORAGE_S3_SECRET_KEY'],
                endpoint_url=app.config.get('STORAGE_S3_ENDPOINT') or None,
                public_url=app.config.get('STORAGE_S3_PUBLIC_URL') or None,
            )
        else:
            self._driver = LocalDriver(
                root=app.config.get('STORAGE_LOCAL_ROOT', 'storage')
            )

    def __getattr__(self, name: str):
        if self._driver is None:
            raise RuntimeError(
                "StorageManager has not been initialized. "
                "Call storage.init_app(app) first."
            )
        return getattr(self._driver, name)
