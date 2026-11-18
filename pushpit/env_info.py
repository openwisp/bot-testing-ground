"""Environment helpers."""

import ctypes.util

import redis


def gdal_available() -> bool:
    """Return True when the GDAL library can be found."""
    return ctypes.util.find_library("gdal") is not None


def remember(key: str, value: str, client: redis.Redis | None = None) -> str:
    """Store a value in Redis and return the stored value."""
    client = client or redis.Redis()
    client.set(key, value)
    return str(client.get(key))
