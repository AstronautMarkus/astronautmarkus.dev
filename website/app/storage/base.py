from abc import ABC, abstractmethod
from typing import List, Union


class StorageDriver(ABC):

    @abstractmethod
    def put(self, path: str, content: Union[bytes, str], **kwargs) -> bool:
        """Write content to the given path."""
        ...

    @abstractmethod
    def get(self, path: str) -> bytes:
        """Read content from the given path."""
        ...

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete the file at the given path."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check whether a file exists at the given path."""
        ...

    @abstractmethod
    def url(self, path: str) -> str:
        """Return the public URL for the given path."""
        ...

    @abstractmethod
    def list(self, prefix: str = '') -> List[str]:
        """List file paths under the given prefix."""
        ...
