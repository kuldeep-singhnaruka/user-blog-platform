"""Tiny in-process TTL cache for public list responses."""

import time

_store: dict[str, tuple[float, object]] = {}


def cached(key: str, ttl_seconds: int, factory):
    if ttl_seconds <= 0:
        return factory()
    now = time.monotonic()
    hit = _store.get(key)
    if hit and hit[0] > now:
        return hit[1]
    value = factory()
    _store[key] = (now + ttl_seconds, value)
    return value


def invalidate_lists() -> None:
    _store.clear()
