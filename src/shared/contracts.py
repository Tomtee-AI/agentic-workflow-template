"""
Shared primitives consumed by every tier — the single schema library.
No tier accepts untyped dicts at its normal interface.
Upgrade: Pydantic v2 BaseModel replaces dataclasses for runtime validation.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskEnvelope(BaseModel):
    """Canonical request produced by Tier 1 and consumed downward."""
    id: UUID = Field(default_factory=uuid4)
    version: str = "1.0"
    intent: str
    payload: dict
    principal: str
    trace_id: UUID = Field(default_factory=uuid4)
    deadline: datetime | None = None
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))


class AgentRequest(BaseModel):
    """Typed input to a specialist agent, including prompt provenance."""
    run_id: UUID
    step_id: str
    agent_id: str
    agent_version: str
    prompt_id: str
    prompt_version: str
    input: dict


class AgentResponse(BaseModel):
    """Typed agent output with cost accounting and optional quorum score."""
    run_id: UUID
    step_id: str
    agent_id: str
    output: dict
    explanation: str | None = None       # human-readable, audit-only
    raw_model_output: str | None = None  # debug/audit only
    consistency_score: float | None = None  # 0.0–1.0; set by quorum dispatcher
    model: str = ""
    prompt_id: str = ""
    prompt_version: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    error: str | None = None

    @property
    def tokens_used(self) -> int:
        return self.tokens_in + self.tokens_out


class ToolCall(BaseModel):
    """Typed tool invocation with idempotency key and operation class."""
    call_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    tool_id: str
    tool_version: str = "1.0.0"
    operation: str = "read"  # "read" | "write" | "destructive"
    input: dict
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))


class ToolResult(BaseModel):
    """Typed tool output including success/error state."""
    call_id: UUID
    tool_id: str
    success: bool
    output: dict | None = None
    error_class: str | None = None
    error_message: str | None = None


class PolicyDecision(BaseModel):
    """Result of a policy engine evaluation."""
    request_id: UUID = Field(default_factory=uuid4)
    allowed: bool
    policy_id: str
    reason: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class HumanApproval(BaseModel):
    """Record of a human-in-the-loop approval request and response."""
    request_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: datetime | None = None
    approved_by: str | None = None
    approved: bool | None = None
    context: dict = Field(default_factory=dict)


class AuditEvent(BaseModel):
    """Immutable event record; redacted at write time before persistence."""
    event_id: UUID = Field(default_factory=uuid4)
    trace_id: UUID
    run_id: UUID
    event_type: str
    actor: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload_hash: str = ""  # SHA-256 of redacted payload
    policy_result: PolicyDecision | None = None
