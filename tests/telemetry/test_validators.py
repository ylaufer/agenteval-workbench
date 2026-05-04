import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.models import SpanRecord, TraceEnvelope
from agenteval.telemetry.validators import (
    load_thresholds,
    main,
    validate_trace_semantics,
    validate_trace_structure,
)


def _span(sid: str, name: str = "span.op", service: str = "svc", kind: str = "INTERNAL",
          start: int = 0, end: int = 10, parent: str | None = None) -> SpanRecord:
    return SpanRecord(sid, parent, name, service, kind, start, end, {})


def _trace(*spans: SpanRecord) -> TraceEnvelope:
    return TraceEnvelope("t1", "simple_rag_query", spans[0].span_id, list(spans))


# --- structure: valid cases ---

def test_structure_valid_for_sample_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    assert validate_trace_structure(trace) == []


def test_structure_valid_single_span() -> None:
    trace = _trace(_span("s1"))
    assert validate_trace_structure(trace) == []


# --- structure: failure cases ---

def test_structure_fails_missing_parent() -> None:
    trace = load_trace(Path("fixtures/traces/malformed_trace_missing_parent.json"))
    errors = validate_trace_structure(trace)
    assert any("missing parent" in e for e in errors)


def test_structure_fails_root_span_missing() -> None:
    span = _span("s1")
    trace = TraceEnvelope("t", "j", "nonexistent-root", [span])
    errors = validate_trace_structure(trace)
    assert any("root span missing" in e for e in errors)


def test_structure_fails_negative_duration() -> None:
    span = SpanRecord("s1", None, "op", "svc", "INTERNAL", 100, 50, {})  # end < start
    trace = _trace(span)
    errors = validate_trace_structure(trace)
    assert any("negative duration" in e for e in errors)


def test_structure_fails_duplicate_span_id() -> None:
    spans = [_span("s1"), _span("s1", name="duplicate.op")]
    trace = TraceEnvelope("t", "j", "s1", spans)
    errors = validate_trace_structure(trace)
    assert any("duplicate span_id" in e for e in errors)


def test_structure_fails_self_parent() -> None:
    span = SpanRecord("s1", "s1", "op", "svc", "INTERNAL", 0, 10, {})
    trace = _trace(span)
    errors = validate_trace_structure(trace)
    assert any("self-parent" in e for e in errors)


def test_structure_fails_orphan_span() -> None:
    # s2 references s1 as parent, but s3 has no parent and is not the root
    s1 = _span("s1")
    s2 = _span("s2", parent="s1")
    s3 = _span("s3")  # no parent, not root
    trace = TraceEnvelope("t", "j", "s1", [s1, s2, s3])
    errors = validate_trace_structure(trace)
    assert any("unreachable span" in e for e in errors)


def test_structure_valid_linear_chain() -> None:
    s1 = _span("s1")
    s2 = _span("s2", parent="s1")
    s3 = _span("s3", parent="s2")
    trace = TraceEnvelope("t", "j", "s1", [s1, s2, s3])
    errors = validate_trace_structure(trace)
    assert errors == []


# --- structure: threshold enforcement ---

def test_structure_threshold_depth_exceeded() -> None:
    thresholds = load_thresholds(Path("config/telemetry_thresholds.yaml"))
    spans = [_span(f"s{i}") for i in range(10)]  # 10 spans, default max is 8
    trace = _trace(*spans)
    errors = validate_trace_structure(trace, thresholds)
    assert any("max_span_count_default" in e for e in errors)


def test_structure_threshold_duration_exceeded() -> None:
    thresholds = load_thresholds(Path("config/telemetry_thresholds.yaml"))
    # default max_total_duration_ms_default is 3000; make a 5000ms trace
    spans = [SpanRecord("s1", None, "op", "svc", "INTERNAL", 0, 5000, {})]
    trace = _trace(*spans)
    errors = validate_trace_structure(trace, thresholds)
    assert any("max_total_duration_ms_default" in e for e in errors)


def test_structure_threshold_not_applied_when_none() -> None:
    # Passing thresholds=None must not trigger threshold checks
    spans = [_span(f"s{i}") for i in range(20)]
    trace = _trace(*spans)
    errors = validate_trace_structure(trace, None)
    # No threshold errors — only structural errors are expected
    assert not any("max_span_count_default" in e for e in errors)


def test_structure_within_thresholds_passes() -> None:
    thresholds = load_thresholds(Path("config/telemetry_thresholds.yaml"))
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    errors = validate_trace_structure(trace, thresholds)
    assert errors == []


# --- semantics: valid cases ---

def test_semantics_valid_for_sample_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    assert validate_trace_semantics(trace) == []


# --- semantics: failure cases ---

def test_semantics_fails_missing_name() -> None:
    span = SpanRecord("s1", None, "", "svc", "INTERNAL", 0, 10, {})
    trace = _trace(span)
    errors = validate_trace_semantics(trace)
    assert any("missing name" in e for e in errors)


def test_semantics_fails_missing_service() -> None:
    span = SpanRecord("s1", None, "op", "", "INTERNAL", 0, 10, {})
    trace = _trace(span)
    errors = validate_trace_semantics(trace)
    assert any("missing service" in e for e in errors)


def test_semantics_fails_missing_kind() -> None:
    span = SpanRecord("s1", None, "op", "svc", "", 0, 10, {})
    trace = _trace(span)
    errors = validate_trace_semantics(trace)
    assert any("missing kind" in e for e in errors)


def test_semantics_multiple_errors_reported() -> None:
    spans = [
        SpanRecord("s1", None, "", "", "", 0, 10, {}),
        SpanRecord("s2", "s1", "", "svc", "INTERNAL", 0, 10, {}),
    ]
    trace = _trace(*spans)
    errors = validate_trace_semantics(trace)
    assert len(errors) >= 4  # s1: name+service+kind, s2: name


# --- main() CLI ---

def test_main_returns_on_valid_trace() -> None:
    with patch.object(sys, "argv", ["agenteval-telemetry-validate", "fixtures/traces/sample_trace.json"]):
        main()  # should return without raising


def test_main_returns_with_thresholds() -> None:
    with patch.object(sys, "argv", [
        "agenteval-telemetry-validate",
        "fixtures/traces/sample_trace.json",
        "--thresholds", "config/telemetry_thresholds.yaml",
    ]):
        main()  # should return without raising


def test_main_exits_one_on_invalid_trace() -> None:
    with patch.object(sys, "argv", [
        "agenteval-telemetry-validate",
        "fixtures/traces/malformed_trace_missing_parent.json",
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1


def test_main_exits_one_on_missing_trace_file() -> None:
    with patch.object(sys, "argv", ["agenteval-telemetry-validate", "nonexistent.json"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1


def test_main_exits_one_on_missing_thresholds_file() -> None:
    with patch.object(sys, "argv", [
        "agenteval-telemetry-validate",
        "fixtures/traces/sample_trace.json",
        "--thresholds", "nonexistent_thresholds.yaml",
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
