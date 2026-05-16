from typing import List, Optional, Union

import boto3
from botocore.exceptions import ClientError

from .base import StorageDriver


class S3Driver(StorageDriver):

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        public_url: Optional[str] = None,
    ):
        self.bucket = bucket
        self._public_url = public_url.rstrip('/') if public_url else None
        self._client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url or None,
        )

    def put(
        self,
        path: str,
        content: Union[bytes, str],
        content_type: str = 'application/octet-stream',
        **kwargs,
    ) -> bool:
        if isinstance(content, str):
            content = content.encode()
        self._client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=content,
            ContentType=content_type,
        )
        return True

    def get(self, path: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=path)
        return response['Body'].read()

    def delete(self, path: str) -> bool:
        self._client.delete_object(Bucket=self.bucket, Key=path)
        return True

    def exists(self, path: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False

    def url(self, path: str) -> str:
        if self._public_url:
            return f"{self._public_url}/{path}"
        return f"https://{self.bucket}.s3.amazonaws.com/{path}"

    def list(self, prefix: str = '') -> List[str]:
        paginator = self._client.get_paginator('list_objects_v2')
        keys: List[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                keys.append(obj['Key'])
        return keys
