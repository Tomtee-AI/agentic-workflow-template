"""
Tier 3 — Specialist Agents: Base Class
All specialist agents are stateless workers. State lives in the Orchestrator
or Tier 5. Each concrete agent declares a capability manifest.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from src.shared.contracts import AgentResponse, TaskEnvelope


@dataclass
class CapabilityManifest:
    capability: str
    version: str
    allowed_tools: list[str]
    input_schema: dict
    output_schema: dict
    cost_class: str     # "low" | "medium" | "high"
    latency_class: str  # "interactive" | "batch" | "background"
    safety_class: str   # "read-only" | "side-effects" | "destructive"


class BaseAgent(ABC):
    manifest: CapabilityManifest  # declared by each subclass

    @abstractmethod
    def run(self, envelope: TaskEnvelope, inputs: dict) -> AgentResponse:
        """Execute the agent's bounded cognitive task and return a typed response."""
