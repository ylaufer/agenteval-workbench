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
    # max_span_count is 6; create 7 spans
    spans = [SpanRecord(f"s{i}", None, f"span.{i}", "svc", "INTERNAL", i, i + 1, {}) for i in range(7)]
    spans[0] = SpanRecord("s0", None, "http.server:/ask", "gw", "SERVER", 0, 100, {})
    trace = TraceEnvelope("t", "simple_rag_query", "s0", spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("max_span_count" in f for f in result.failures)


def test_conformance_fails_required_order_violated() -> None:
    # simple_rag_query requires order: http.server:/ask → retriever.search → llm.generate
    # Swap retriever.search and llm.generate
    spans = [
        _span("s1", "http.server:/ask", start=0, end=10),
        _span("s2", "llm.generate", start=11, end=20),
        _span("s3", "retriever.search", start=21, end=30),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("span order violated" in f for f in result.failures)


def test_conformance_passes_correct_order() -> None:
    spans = [
        _span("s1", "http.server:/ask", start=0, end=10),
        _span("s2", "retriever.search", start=11, end=20),
        _span("s3", "llm.generate", start=21, end=30),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is True


def test_conformance_result_has_trace_id() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.trace_id == trace.trace_id


def test_conformance_no_spec_has_trace_id() -> None:
    spans = [_span("s1", "some.span")]
    trace = TraceEnvelope("trace-xyz", "unknown_journey", "s1", spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.trace_id == "trace-xyz"


def test_conformance_fails_max_occurrences_exceeded() -> None:
    # max_occurrences: llm.generate: 2; put 3 occurrences
    spans = [
        _span("s1", "http.server:/ask"),
        _span("s2", "retriever.search"),
        _span("s3", "llm.generate"),
        _span("s4", "llm.generate"),
        _span("s5", "llm.generate"),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("at most" in f for f in result.failures)


def test_conformance_fails_min_occurrences_not_met() -> None:
    # min_occurrences: retriever.search: 1; omit it entirely
    spans = [
        _span("s1", "http.server:/ask"),
        _span("s2", "llm.generate"),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is False
    assert any("at least" in f for f in result.failures)


def test_conformance_passes_occurrence_bounds_satisfied() -> None:
    # 1x retriever.search (≥1), 1x llm.generate (≤2) — within bounds
    spans = [
        _span("s1", "http.server:/ask", start=0, end=10),
        _span("s2", "retriever.search", start=11, end=20),
        _span("s3", "llm.generate", start=21, end=30),
    ]
    trace = _make_trace(spans)
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is True


def test_conformance_metrics_populated() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert "span_count" in result.metrics
    assert "total_duration_ms" in result.metrics
    assert result.metrics["span_count"] == 3
