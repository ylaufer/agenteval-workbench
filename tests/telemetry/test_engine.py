from pathlib import Path

import pytest

from agenteval.telemetry.engine import evaluate_conformance
from agenteval.telemetry.invariants import load_invariants
from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.models import SpanRecord, TraceEnvelope


def _make_trace(spans: list[SpanRecord], journey: str = "simple_rag_query") -> TraceEnvelope:
    return TraceEnvelope(
        trace_id="t-test",
        journey=journey,
        root_span_id=spans[0].span_id if spans else "s1",
        spans=spans,
    )


def _span(sid: str, name: str, start: int = 0, end: int = 10) -> SpanRecord:
    return SpanRecord(sid, None, name, "svc", "INTERNAL", start, end, {})


def test_conformance_passes_for_sample_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is True
    assert result.failures == []


def test_conformance_fails_no_invariant_spec() -> None:
    trace = _make_trace([_span("s1", "some.span")], journey="unknown_journey")
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("no invariant spec found" in f for f in result.failures)


def test_conformance_fails_missing_required_span() -> None:
    # simple_rag_query requires retriever.search — omit it
    spans = [
        _span("s1", "http.server:/ask"),
        _span("s2", "llm.generate"),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("missing required span" in f for f in result.failures)


def test_conformance_fails_forbidden_span_present() -> None:
    # simple_rag_query forbids support_ticket.create
    spans = [
        _span("s1", "http.server:/ask"),
        _span("s2", "retriever.search"),
        _span("s3", "llm.generate"),
        _span("s4", "support_ticket.create"),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("forbidden span present" in f for f in result.failures)


def test_conformance_fails_duration_exceeded() -> None:
    # max_total_duration_ms is 2500; make a trace that exceeds it
    spans = [
        SpanRecord("s1", None, "http.server:/ask", "gw", "SERVER", 0, 3000, {}),
        SpanRecord("s2", "s1", "retriever.search", "r", "INTERNAL", 10, 100, {}),
        SpanRecord("s3", "s1", "llm.generate", "llm", "INTERNAL", 101, 200, {}),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("max total duration" in f for f in result.failures)


def test_conformance_fails_depth_exceeded() -> None:
    # max_depth is 6; create 7 spans
    spans = [SpanRecord(f"s{i}", None, f"span.{i}", "svc", "INTERNAL", i, i + 1, {}) for i in range(7)]
    spans[0] = SpanRecord("s0", None, "http.server:/ask", "gw", "SERVER", 0, 100, {})
    trace = TraceEnvelope("t", "simple_rag_query", "s0", spans)
    # Patch required spans to avoid that failure
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("max depth" in f for f in result.failures)


def test_conformance_metrics_populated() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert "span_count" in result.metrics
    assert "total_duration_ms" in result.metrics
    assert result.metrics["span_count"] == 3
