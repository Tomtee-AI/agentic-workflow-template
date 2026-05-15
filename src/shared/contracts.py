"""
Shared primitives consumed by every tier.
All inter-tier data transfer uses these types — never ad-hoc dicts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class TaskEnvelope:
    """Canonical request shape produced by Tier 1 and consumed downward."""
    intent: str
    payload: dict[str, Any]
    principal: str                          # authenticated user/system identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deadline: float | None = None           # unix timestamp


@dataclass
class ToolCall:
    tool_name: str
    arguments: dict[str, Any]
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ToolResult:
    tool_name: str
    idempotency_key: str
    output: Any
    error: str | None = None
    success: bool = True


@dataclass
class AgentResponse:
    agent_id: str
    run_id: str
    output: Any
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: str | None = None
