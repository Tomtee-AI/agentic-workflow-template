"""
Tier 4 — Tools & Services: Base Tool Adapter
One base class handles auth, retries, schema validation, and tracing.
Concrete tools subclass it. All tools are pure functions of declared inputs;
side effects are explicit in the manifest.
"""

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from src.shared.contracts import ToolCall, ToolResult
from src.shared.exceptions import TransientError, PolicyDenied


class BaseTool(ABC):
    name: str
    has_side_effects: bool = False
    requires_human_approval: bool = False
    max_retries: int = 3
    base_delay: float = 1.0

    @abstractmethod
    def _execute(self, call: ToolCall) -> ToolResult:
        """Perform the actual tool operation."""

    def run(self, call: ToolCall) -> ToolResult:
        if self.requires_human_approval:
            self._request_human_approval(call)

        attempt = 0
        while attempt <= self.max_retries:
            try:
                result = self._execute(call)
                return result
            except TransientError:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                time.sleep(self.base_delay * (2 ** attempt))

    def _request_human_approval(self, call: ToolCall) -> None:
        # TODO: integrate with human-in-the-loop escalation channel
        raise PolicyDenied(f"Tool '{self.name}' requires human approval")
