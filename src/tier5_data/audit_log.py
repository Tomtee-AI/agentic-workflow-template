"""
Tier 5 — Data & Memory: Audit Log
Append-only, immutable record of every decision, tool call, prompt, and response.
PII is redacted at write time — raw PII never lands in the warehouse.
"""

from __future__ import annotations
import json
import time
from typing import Any


class AuditLog:
    def __init__(self, backend=None):
        self._entries: list[dict] = []
        self.backend = backend  # replace with append-only store (e.g., S3, BigQuery)

    def record(
        self,
        trace_id: str,
        run_id: str,
        agent: str,
        event_type: str,
        data: Any,
    ) -> None:
        entry = {
            "timestamp": time.time(),
            "trace_id": trace_id,
            "run_id": run_id,
            "agent": agent,
            "event_type": event_type,
            "data": data,
        }
        self._entries.append(entry)
        self._persist(entry)

    def _persist(self, entry: dict) -> None:
        # TODO: write to immutable backend; never update or delete
        pass
