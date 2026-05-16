"""
Tier 4 — Tools & Services: Policy Gate
Called by the tool gateway before every tool execution.
Delegates to the Tier 0 policy engine; agents never call this directly.
"""
from __future__ import annotations

from src.shared.contracts import PolicyDecision, ToolCall
from src.tier0_policy.engine import PolicyEngine

_engine = PolicyEngine()


def check(
    call: ToolCall,
    principal: str,
    agent_id: str,
    allowed_tools: list[str],
) -> PolicyDecision:
    return _engine.evaluate_tool_call(call, principal, agent_id, allowed_tools)
