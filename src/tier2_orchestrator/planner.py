"""
Tier 2 — Orchestrator: Planner
Decomposes a TaskEnvelope intent into an ordered DAG of steps.
Can be LLM-driven, deterministic rules-based, or a hybrid.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from src.shared.contracts import TaskEnvelope


@dataclass
class Step:
    step_id: str
    agent_capability: str       # key into capability registry
    inputs: dict
    depends_on: list[str] = field(default_factory=list)


@dataclass
class WorkflowPlan:
    run_id: str
    steps: list[Step]
    budget_tokens: int = 100_000
    budget_usd: float = 5.0
    budget_seconds: float = 300.0


class Planner:
    def plan(self, envelope: TaskEnvelope) -> WorkflowPlan:
        """Produce a WorkflowPlan from a TaskEnvelope."""
        raise NotImplementedError
