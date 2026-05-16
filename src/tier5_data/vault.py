"""
Tier 5 — Data & Memory: Secret Vault Interface
Agents receive scoped, JIT, time-bound tokens per tool call.
Raw secrets never appear in prompts, logs, or environment variables.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ScopedToken:
    token: str
    scope: str
    expires_at: datetime
    principal: str
    tool_id: str

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at


class BaseVault(ABC):
    @abstractmethod
    def issue_token(self, principal: str, tool_id: str, operation: str) -> ScopedToken:
        """Issue a short-lived, scoped token for a single tool call."""

    @abstractmethod
    def revoke_token(self, token: str) -> None:
        """Revoke a token before its natural expiry."""


class StubVault(BaseVault):
    """In-process stub for local development. Replace with HashiCorp Vault or AWS SM."""

    def issue_token(self, principal: str, tool_id: str, operation: str) -> ScopedToken:
        return ScopedToken(
            token=f"stub-{principal}-{tool_id}",
            scope=f"{tool_id}:{operation}",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            principal=principal,
            tool_id=tool_id,
        )

    def revoke_token(self, token: str) -> None:
        pass
