from pathlib import Path

from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.validators import validate_trace_structure, validate_trace_semantics


def test_structure_valid_for_sample_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    assert validate_trace_structure(trace) == []


def test_structure_fails_missing_parent() -> None:
    trace = load_trace(Path("fixtures/traces/malformed_trace_missing_parent.json"))
    errors = validate_trace_structure(trace)
    assert any("missing parent" in e for e in errors)


def test_semantics_valid_for_sample_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    assert validate_trace_semantics(trace) == []
