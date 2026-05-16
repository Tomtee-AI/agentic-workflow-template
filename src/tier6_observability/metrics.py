"""
Tier 6 — Observability: Metrics
System, product, and AI-specific metric names and an in-process store.
Replace MetricStore with a Prometheus client or OTLP exporter in production.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricStore:
    _counters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    _gauges: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        self._counters[_key(name, labels)] += value

    def gauge(self, name: str, value: float, **labels: str) -> None:
        self._gauges[_key(name, labels)] = value

    def get(self, name: str, **labels: str) -> float:
        k = _key(name, labels)
        return self._counters.get(k, self._gauges.get(k, 0.0))


def _key(name: str, labels: dict[str, str]) -> str:
    suffix = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    return f"{name}{{{suffix}}}" if suffix else name


# Module-level singleton; swap for Prometheus registry in production.
METRICS = MetricStore()

# --- Canonical metric names ---

# System
TASK_SUCCESS = "task_success_total"
TASK_FAILURE = "task_failure_total"
COST_USD = "model_cost_usd_total"
TOKENS_TOTAL = "model_tokens_total"
RETRY_TOTAL = "step_retry_total"
CIRCUIT_OPEN = "circuit_breaker_open"

# Product / quality
HUMAN_ESCALATIONS = "human_escalation_total"
SCHEMA_REPAIRS = "schema_repair_total"
POLICY_DENIALS = "policy_denial_total"
USER_CORRECTIONS = "user_correction_total"
REPLAY_PASS = "replay_test_pass_total"

# AI-specific
CONSISTENCY_SCORE = "quorum_consistency_score"
EVAL_SCORE = "eval_score"
HALLUCINATION_SCORE = "hallucination_score"
FAITHFULNESS_SCORE = "faithfulness_score"

# Sustainability
CARBON_GCO2 = "carbon_cost_gco2_total"
