"""
Tier 5 — Data & Memory: Long-Term Memory
Persisted across runs. Explicit write paths and TTLs required.
Tenant-isolated — never mix tenants in a shared index.
"""

from __future__ import annotations
from typing import Any


class LongTermMemory:
    def __init__(self, tenant_id: str, backend=None):
        self.tenant_id = tenant_id
        self._store: dict[str, dict] = {}
        self.backend = backend  # replace with vector + relational store

    def write(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        self._store[key] = {"value": value, "ttl": ttl_seconds}
        self._persist(key)

    def read(self, key: str) -> Any | None:
        entry = self._store.get(key)
        return entry["value"] if entry else None

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def _persist(self, key: str) -> None:
        # TODO: write to durable backend with tenant namespace
        pass
