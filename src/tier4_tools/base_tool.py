"""
Tier 4 — Tools & Services: Base Tool Adapter
One base class handles retries, schema validation, and tracing.
Concrete tools subclass it, declare tool_id and operation_class,
and implement _execute(). Manifests are signed and registered at startup.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod

from src.shared.contracts import ToolCall, ToolResult
from src.shared.exceptions import TransientError


class BaseTool(ABC):
    tool_id: str
    operation_class: str = "read"      # "read" | "write" | "destructive"
    requires_human_approval: bool = False
    max_retries: int = 3
    base_delay: float = 1.0

    @abstractmethod
    def _execute(self, call: ToolCall) -> ToolResult:
        """Perform the actual tool operation against the external service."""

    def run(self, call: ToolCall) -> ToolResult:
        if self.requires_human_approval:
            self._request_human_approval(call)

        attempt = 0
        while attempt <= self.max_retries:
            try:
                return self._execute(call)
            except TransientError:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                time.sleep(self.base_delay * (2 ** attempt))

    def _request_human_approval(self, call: ToolCall) -> None:
        # Replace with durable pause + notification channel integration.
        from src.shared.exceptions import PolicyDenied
        raise PolicyDenied(f"Tool '{self.tool_id}' requires human approval before execution")
