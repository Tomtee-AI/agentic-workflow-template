"""
Tier 6 — Observability: Guardrails
Validates every LLM response before it can trigger a tool call.
Treats the LLM as a confused deputy — its output alone never authorizes action.
"""

from __future__ import annotations
from src.shared.contracts import AgentResponse, ToolCall
from src.shared.exceptions import PolicyDenied, SchemaValidationError


class Guardrail:
    def validate_response(self, response: AgentResponse) -> None:
        """Raise SchemaValidationError if the response fails schema checks."""
        if response.output is None:
            raise SchemaValidationError("Agent returned null output")

    def validate_tool_call(self, call: ToolCall, policy: dict) -> None:
        """Raise PolicyDenied if the tool call violates policy."""
        blocked = policy.get("blocked_tools", [])
        if call.tool_name in blocked:
            raise PolicyDenied(f"Tool '{call.tool_name}' is blocked by policy")

    def check_prompt_injection(self, text: str) -> str:
        """Strip patterns that look like injected instructions from retrieved content."""
        # TODO: implement heuristic + model-based injection detection
        return text
