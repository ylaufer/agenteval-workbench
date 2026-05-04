from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpanRecord:
    span_id: str
    parent_span_id: str | None
    name: str
    service: str
    kind: str
    start_ms: int
    end_ms: int
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceEnvelope:
    trace_id: str
    journey: str
    root_span_id: str
    spans: list[SpanRecord]


@dataclass
class ConformanceResult:
    journey: str
    passed: bool
    failures: list[str]
    trace_id: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
