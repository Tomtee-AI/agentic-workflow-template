"""
Tier 2 — Orchestrator: State Machine
Thin driver over WorkflowRun that exposes step-level status tracking.
The Orchestrator is the ONLY component allowed to call transition().
"""
from __future__ import annotations

from enum import Enum

from src.tier2_orchestrator.workflow_run import RunState, WorkflowRun


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"


class WorkflowStateMachine:
    def __init__(self, run_id: str, store: object = None):
        self.run = WorkflowRun()
        self._steps: dict[str, dict] = {}
        self._store = store

    def start(self, actor: str = "orchestrator") -> None:
        self.run.transition(RunState.RUNNING, actor=actor, reason="Workflow started")

    def transition(self, step_id: str, status: StepStatus, output: object = None) -> None:
        self._steps[step_id] = {"status": status, "output": output}
        # Mirror step completion into the run-level state machine.
        if status == StepStatus.FAILED:
            self.run.transition(
                RunState.FAILED,
                actor="state_machine",
                reason=f"Step '{step_id}' failed",
                output_payload=output,
            )
        elif status == StepStatus.COMPLETED:
            self.run.transition(
                RunState.RUNNING,
                actor="state_machine",
                reason=f"Step '{step_id}' completed",
                output_payload=output,
            )

    def get_status(self, step_id: str) -> StepStatus:
        return self._steps.get(step_id, {}).get("status", StepStatus.PENDING)

    def complete(self, actor: str = "orchestrator") -> None:
        self.run.transition(RunState.COMPLETED, actor=actor, reason="All steps completed")

    def wait_for_human(self, actor: str = "orchestrator", reason: str = "") -> None:
        self.run.transition(RunState.WAITING_FOR_HUMAN, actor=actor, reason=reason)
