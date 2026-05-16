"""
Tier 0 — Governance & Policy: Feature Flags
Per-tenant and per-workflow flags govern shadow, canary, and GA
promotion of new agents and tools. No Orchestrator code changes on promotion.
"""
from __future__ import annotations

from enum import Enum


class FlagState(str, Enum):
    DISABLED = "disabled"
    SHADOW = "shadow"    # runs but result is discarded
    CANARY = "canary"    # routes a configurable fraction of traffic
    ENABLED = "enabled"


_FLAGS: dict[str, FlagState] = {}


def set_flag(name: str, state: FlagState) -> None:
    _FLAGS[name] = state


def get_flag(name: str) -> FlagState:
    return _FLAGS.get(name, FlagState.DISABLED)


def is_enabled(name: str) -> bool:
    return get_flag(name) == FlagState.ENABLED


def is_shadow(name: str) -> bool:
    return get_flag(name) == FlagState.SHADOW
