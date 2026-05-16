"""
Tier 6 — Observability: Distributed Tracing
Every span tagged with trace_id, run_id, step_id, agent, tool, model,
prompt provenance, tokens, cost, latency, consistency_score, and policy result.
Replace Tracer._export() with an OTLP/Jaeger/Datadog exporter in production.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Span:
    name: str
    trace_id: str
    run_id: str
    step_id: str = ""
    agent_id: str = ""
    tool_id: str = ""
    model: str = ""
    prompt_id: str = ""
    prompt_version: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    retry_count: int = 0
    validation_result: str = ""   # "pass" | "fail" | "repaired"
    policy_result: str = ""       # "allowed" | "denied"
    consistency_score: float | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    error: str | None = None

    @property
    def latency_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


class Tracer:
    def __init__(self, exporter: object = None):
        self.exporter = exporter

    @contextmanager
    def span(self, name: str, **kwargs) -> Iterator[Span]:
        s = Span(name=name, **kwargs)
        try:
            yield s
        except Exception as exc:
            s.error = str(exc)
            raise
        finally:
            s.end_time = time.time()
            self._export(s)

    def _export(self, span: Span) -> None:
        # Replace with: self.exporter.export(span) → OTLP / Jaeger / Datadog
        pass
