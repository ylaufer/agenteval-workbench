from pathlib import Path

from agenteval.telemetry.loader import load_trace


def test_load_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    assert trace.trace_id == "trace-001"
    assert len(trace.spans) == 3
