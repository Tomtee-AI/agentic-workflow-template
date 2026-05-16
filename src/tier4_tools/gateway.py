"""
Tier 4 — Tools & Services: Tool Gateway
Central enforcement point for tool discovery, schema validation,
policy check, auth, idempotency, and audit — in that order.
Agents never call tools directly; every call flows through here.
"""
from __future__ import annotations

from src.shared.contracts import AuditEvent, PolicyDecision, ToolCall, ToolResult
from src.shared.exceptions import PolicyDenied
from src.tier0_policy import engine as _policy_engine_module
from src.tier4_tools.base_tool import BaseTool

_TOOL_REGISTRY: dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    _TOOL_REGISTRY[tool.tool_id] = tool


def call_tool(
    call: ToolCall,
    principal: str,
    agent_id: str,
    allowed_tools: list[str],
    audit_fn: object = None,  # callable(AuditEvent) | None
) -> ToolResult:
    """Execute a tool call through the full policy → auth → audit pipeline."""
    _engine = _policy_engine_module.PolicyEngine()
    decision: PolicyDecision = _engine.evaluate_tool_call(
        call, principal, agent_id, allowed_tools
    )

    if audit_fn is not None:
        import hashlib, json
        raw = json.dumps(call.model_dump(), default=str, sort_keys=True).encode()
        event = AuditEvent(
            trace_id=call.run_id,
            run_id=call.run_id,
            event_type="tool_call_evaluated",
            actor=agent_id,
            payload_hash=hashlib.sha256(raw).hexdigest()[:16],
            policy_result=decision,
        )
        audit_fn(event)

    if not decision.allowed:
        raise PolicyDenied(decision.reason)

    tool = _TOOL_REGISTRY.get(call.tool_id)
    if tool is None:
        raise LookupError(f"Tool not found in registry: {call.tool_id}")

    return tool.run(call)
