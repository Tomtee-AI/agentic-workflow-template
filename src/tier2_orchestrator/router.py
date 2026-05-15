"""
Tier 2 — Orchestrator: Router
Selects the correct Specialist Agent for each step by consulting the
capability registry. New agents self-register; the Orchestrator code
does not change when new agents are added.
"""

from __future__ import annotations
from src.tier2_orchestrator.planner import Step


_CAPABILITY_REGISTRY: dict[str, type] = {}


def register_agent(capability: str, agent_cls: type) -> None:
    _CAPABILITY_REGISTRY[capability] = agent_cls


def route(step: Step):
    agent_cls = _CAPABILITY_REGISTRY.get(step.agent_capability)
    if agent_cls is None:
        raise LookupError(f"No agent registered for capability: {step.agent_capability}")
    return agent_cls()
