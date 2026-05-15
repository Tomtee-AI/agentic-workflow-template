"""
Tier 5 — Data & Memory: Short-Term Memory
Per-run scratchpad, bounded in size and discarded at run end.
Never persists across runs.
"""

from typing import Any


class ShortTermMemory:
    def __init__(self, run_id: str, max_entries: int = 500):
        self.run_id = run_id
        self._store: list[dict] = []
        self.max_entries = max_entries

    def append(self, role: str, content: Any) -> None:
        if len(self._store) >= self.max_entries:
            self._store.pop(0)  # sliding window
        self._store.append({"role": role, "content": content})

    def as_messages(self) -> list[dict]:
        return list(self._store)

    def clear(self) -> None:
        self._store.clear()
