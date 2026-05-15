"""
Caching layer for prompt-responses, tool results, and embeddings.
Keys are content-addressed to ensure invalidation on prompt/tool/model change.
"""

import hashlib
import json
from typing import Any


def content_hash(*parts: Any) -> str:
    serialized = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


class PromptResponseCache:
    """Keyed by (model, prompt_hash, tool_set_hash, retrieval_hash)."""

    def __init__(self, backend=None):
        self._store: dict[str, Any] = {}
        self.backend = backend  # replace with Redis/Memcached in production

    def get(self, model: str, prompt: str, tool_set: list, retrieval: list) -> Any | None:
        key = content_hash(model, prompt, tool_set, retrieval)
        return self._store.get(key)

    def set(self, model: str, prompt: str, tool_set: list, retrieval: list, value: Any) -> None:
        key = content_hash(model, prompt, tool_set, retrieval)
        self._store[key] = value


class EmbeddingCache:
    """Never re-embed the same chunk; keyed by content hash + model version."""

    def __init__(self, backend=None):
        self._store: dict[str, list[float]] = {}
        self.backend = backend

    def get(self, text: str, model_version: str) -> list[float] | None:
        return self._store.get(content_hash(text, model_version))

    def set(self, text: str, model_version: str, embedding: list[float]) -> None:
        self._store[content_hash(text, model_version)] = embedding
