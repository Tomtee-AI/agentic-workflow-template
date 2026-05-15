"""
Tier 4 — Tools & Services: Tool Gateway
Central registry for tool discovery, schema enforcement, auth, and audit.
Agents never call tools directly — they go through this gateway.
Destructive operations require an explicit policy gate.
"""

from __future__ import annotations
from src.shared.contracts import ToolCall, ToolResult
from src.shared.exceptions import PolicyDenied
from src.tier4_tools.base_tool import BaseTool


_TOOL_REGISTRY: dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    _TOOL_REGISTRY[tool.name] = tool


def call_tool(call: ToolCall, principal: str, allowed_tools: list[str]) -> ToolResult:
    if call.tool_name not in allowed_tools:
        raise PolicyDenied(
            f"Agent not permitted to call '{call.tool_name}'. "
            f"Allowed: {allowed_tools}"
        )
    tool = _TOOL_REGISTRY.get(call.tool_name)
    if tool is None:
        raise LookupError(f"Tool not found: {call.tool_name}")
    # TODO: emit audit log entry before execution
    return tool.run(call)
