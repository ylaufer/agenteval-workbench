from pathlib import Path

from agenteval.telemetry.engine import evaluate_conformance
from agenteval.telemetry.invariants import load_invariants
from agenteval.telemetry.loader import load_trace


def test_conformance_passes_for_sample_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    assert result.passed is True
