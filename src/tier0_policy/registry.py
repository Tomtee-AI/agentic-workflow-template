"""
Tier 0 — Governance & Policy: Capability Registry
Single source of truth for every agent, tool, prompt, and model.
Routing decisions consult this registry at run time — no hardcoded routing.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CapabilityManifest:
    id: str
    version: str
    allowed_tools: list[str]
    input_schema: dict
    output_schema: dict
    cost_class: str = "low"           # "low" | "medium" | "high"
    latency_class: str = "medium"     # "fast" | "medium" | "slow"
    safety_class: str = "standard"    # "standard" | "elevated" | "restricted"
    data_access: list[str] = field(default_factory=lambda: ["public"])
    quorum_required: bool = False
    quorum_min_instances: int = 3
    quorum_threshold: float = 0.7
    requires_human_approval: bool = False
    max_runtime_seconds: int = 120
    max_tool_calls: int = 20


_AGENT_REGISTRY: dict[str, type] = {}
_MANIFEST_REGISTRY: dict[str, CapabilityManifest] = {}


def register_agent(
    capability: str,
    cls: type,
    manifest: CapabilityManifest | None = None,
) -> None:
    _AGENT_REGISTRY[capability] = cls
    if manifest is not None:
        _MANIFEST_REGISTRY[capability] = manifest


def get_agent(capability: str) -> type:
    agent_cls = _AGENT_REGISTRY.get(capability)
    if agent_cls is None:
        raise LookupError(f"No agent registered for capability: {capability}")
    return agent_cls


def get_manifest(capability: str) -> CapabilityManifest | None:
    return _MANIFEST_REGISTRY.get(capability)


def list_capabilities() -> list[str]:
    return list(_AGENT_REGISTRY.keys())
