from pathlib import Path

from agenteval.telemetry.engine import evaluate_conformance
from agenteval.telemetry.invariants import load_invariants
from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.reporters import write_json_report, write_markdown_report


def test_reporters_write_files(tmp_path: Path) -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    invariants = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    result = evaluate_conformance(trace, invariants)
    out_json = tmp_path / "report.json"
    out_md = tmp_path / "report.md"
    write_json_report(result, out_json)
    write_markdown_report(result, out_md)
    assert out_json.exists()
    assert out_md.exists()
