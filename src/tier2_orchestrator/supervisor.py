"""
Tier 2 — Orchestrator: Supervisor
Monitors budget consumption and enforces per-step and per-run limits.
Triggers human escalation when defined thresholds are crossed.
"""

from src.shared.contracts import AgentResponse
from src.shared.exceptions import BudgetExceeded
from src.tier2_orchestrator.planner import WorkflowPlan


class Supervisor:
    def __init__(self, plan: WorkflowPlan):
        self.plan = plan
        self._tokens_used = 0
        self._cost_usd = 0.0

    def record(self, response: AgentResponse) -> None:
        self._tokens_used += response.tokens_used
        self._cost_usd += response.cost_usd
        self._check_budgets()

    def _check_budgets(self) -> None:
        if self._tokens_used > self.plan.budget_tokens:
            raise BudgetExceeded(f"Token budget exceeded: {self._tokens_used}")
        if self._cost_usd > self.plan.budget_usd:
            raise BudgetExceeded(f"Cost budget exceeded: ${self._cost_usd:.4f}")

    def escalate_to_human(self, reason: str) -> None:
        # TODO: pause workflow, persist state, notify via configured channel
        raise NotImplementedError(f"Human escalation required: {reason}")
