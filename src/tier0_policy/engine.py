"""
Tier 0 — Governance & Policy: Policy Engine
Evaluates tool calls and workflow actions against declared policy rules.
Enforcement is by code, never by prompt instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from src.shared.contracts import PolicyDecision, ToolCall


@dataclass
class PolicyRule:
    rule_id: str
    description: str
    enforcement: str  # "deny" | "deny_until_approved" | "require"


class PolicyEngine:
    def __init__(self, rules: list[PolicyRule] | None = None):
        self._rules = rules or []

    def evaluate_tool_call(
        self,
        call: ToolCall,
        principal: str,
        agent_id: str,
        allowed_tools: list[str],
    ) -> PolicyDecision:
        if call.tool_id not in allowed_tools:
            return PolicyDecision(
                allowed=False,
                policy_id="agent_tool_allowlist",
                reason=(
                    f"Agent '{agent_id}' not permitted to call '{call.tool_id}'. "
                    f"Allowed: {allowed_tools}"
                ),
            )
        if call.operation == "destructive":
            return PolicyDecision(
                allowed=False,
                policy_id="destructive_requires_approval",
                reason="Destructive operations require explicit human approval gate.",
            )
        return PolicyDecision(
            allowed=True,
            policy_id="default_allow",
            reason="All checks passed.",
        )

    def requires_human_approval(self, call: ToolCall) -> bool:
        return call.operation == "destructive"
