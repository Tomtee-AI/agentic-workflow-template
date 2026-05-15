"""
Tier 6 — Observability: Distributed Tracing
Every span tagged with trace_id, run_id, agent, tool, model, tokens, cost, latency.
"""

from __future__ import annotations
import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    trace_id: str
    run_id: str
    agent: str = ""
    tool: str = ""
    model: str = ""
    tokens: int = 0
    cost_usd: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    error: str | None = None

    @property
    def latency_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


class Tracer:
    def __init__(self, exporter=None):
        self.exporter = exporter  # replace with OTLP/Jaeger/Datadog exporter

    @contextmanager
    def span(self, name: str, **kwargs):
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
        # TODO: send to tracing backend
        pass
