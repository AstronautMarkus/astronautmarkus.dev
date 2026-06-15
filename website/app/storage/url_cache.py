import threading
import time
from typing import Callable, Dict, Tuple

_lock = threading.Lock()
_cache: Dict[str, Tuple[str, float]] = {}


def get_or_set(key: str, ttl: int, factory: Callable[[], str]) -> str:
    """Return the cached value for `key`, or compute and cache it via `factory`."""
    now = time.monotonic()

    cached = _cache.get(key)
    if cached and cached[1] > now:
        return cached[0]

    with _lock:
        cached = _cache.get(key)
        if cached and cached[1] > now:
            return cached[0]

        value = factory()
        _cache[key] = (value, now + ttl)
        return value
