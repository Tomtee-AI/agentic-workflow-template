"""
Tier 2 — Orchestrator: Workflow Run
Full durable run record with 10-state machine and structured transition history.
The Orchestrator is the ONLY component that calls transition().
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class RunState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class StateTransition:
    previous: RunState
    next: RunState
    timestamp: datetime
    actor: str
    reason: str
    input_hash: str
    output_hash: str
    policy_result: str | None = None
    trace_id: str | None = None


@dataclass
class WorkflowRun:
    run_id: UUID = field(default_factory=uuid4)
    state: RunState = field(default=RunState.RECEIVED)
    history: list[StateTransition] = field(default_factory=list)
    _store: object = field(default=None, repr=False)

    def transition(
        self,
        next_state: RunState,
        actor: str,
        reason: str,
        input_payload: object = None,
        output_payload: object = None,
        policy_result: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        record = StateTransition(
            previous=self.state,
            next=next_state,
            timestamp=datetime.utcnow(),
            actor=actor,
            reason=reason,
            input_hash=_sha256(input_payload),
            output_hash=_sha256(output_payload),
            policy_result=policy_result,
            trace_id=trace_id,
        )
        self.history.append(record)
        self.state = next_state
        self._persist(record)

    def _persist(self, record: StateTransition) -> None:
        # Replace with write to durable store (Temporal, relational DB).
        pass


def _sha256(obj: object) -> str:
    if obj is None:
        return ""
    raw = json.dumps(obj, default=str, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]
