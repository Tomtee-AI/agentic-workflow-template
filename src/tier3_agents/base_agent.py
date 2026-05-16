"""
Tier 3 — Specialist Agents: Base Class
All specialist agents are stateless workers. State lives in the Orchestrator
or Tier 5. Each concrete agent declares a CapabilityManifest from Tier 0.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.shared.contracts import AgentRequest, AgentResponse
from src.tier0_policy.registry import CapabilityManifest  # noqa: F401 — re-exported


class BaseAgent(ABC):
    manifest: CapabilityManifest  # declared as a class attribute by each subclass

    @abstractmethod
    def run(self, request: AgentRequest) -> AgentResponse:
        """Execute the agent's bounded cognitive task and return a typed response.

        The Orchestrator routes through the quorum dispatcher if
        manifest.quorum_required is True — agents never self-dispatch quorum.
        """
