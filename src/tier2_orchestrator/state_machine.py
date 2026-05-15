"""
Tier 2 — Orchestrator: State Machine
Durable, idempotent workflow state persisted to Tier 5.
The Orchestrator is the ONLY component allowed to mutate workflow state.
"""

from __future__ import annotations
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"


class WorkflowStateMachine:
    def __init__(self, run_id: str, store=None):
        self.run_id = run_id
        self._store = store or {}   # replace with durable backend (Temporal, DB)

    def transition(self, step_id: str, status: StepStatus, output=None) -> None:
        self._store[step_id] = {"status": status, "output": output}
        self._persist()

    def get_status(self, step_id: str) -> StepStatus:
        return self._store.get(step_id, {}).get("status", StepStatus.PENDING)

    def _persist(self) -> None:
        # TODO: write to durable store (Tier 5)
        pass
