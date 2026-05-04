import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from agenteval.telemetry.engine import evaluate_conformance
from agenteval.telemetry.invariants import load_invariants
from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.models import ConformanceResult
from agenteval.telemetry.reporters import main, write_json_report, write_markdown_report


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


def test_json_report_content(tmp_path: Path) -> None:
    import json
    result = ConformanceResult(
        journey="test_journey",
        passed=False,
        failures=["missing required span: foo"],
        metrics={"span_count": 2, "total_duration_ms": 50},
    )
    out = tmp_path / "r.json"
    write_json_report(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["journey"] == "test_journey"
    assert data["passed"] is False
    assert data["failures"] == ["missing required span: foo"]
    assert data["metrics"]["span_count"] == 2


def test_markdown_report_passing(tmp_path: Path) -> None:
    result = ConformanceResult(
        journey="simple_rag_query",
        passed=True,
        failures=[],
        metrics={"span_count": 3, "total_duration_ms": 180},
    )
    out = tmp_path / "r.md"
    write_markdown_report(result, out)
    content = out.read_text(encoding="utf-8")
    assert "# Conformance Report: simple_rag_query" in content
    assert "Passed: True" in content
    assert "span_count: 3" in content
    assert "total_duration_ms: 180" in content
    assert "## Failures" in content
    assert "- None" in content


def test_markdown_report_with_failures(tmp_path: Path) -> None:
    result = ConformanceResult(
        journey="simple_rag_query",
        passed=False,
        failures=["missing required span: retriever.search", "trace exceeds max total duration"],
        metrics={"span_count": 1, "total_duration_ms": 5000},
    )
    out = tmp_path / "r.md"
    write_markdown_report(result, out)
    content = out.read_text(encoding="utf-8")
    assert "Passed: False" in content
    assert "missing required span: retriever.search" in content
    assert "trace exceeds max total duration" in content
    # metrics rendered as key-value lines, not Python repr
    assert "span_count: 1" in content
    assert "{" not in content


def test_markdown_report_empty_metrics(tmp_path: Path) -> None:
    result = ConformanceResult(journey="j", passed=True, failures=[], metrics={})
    out = tmp_path / "r.md"
    write_markdown_report(result, out)
    content = out.read_text(encoding="utf-8")
    assert "(none)" in content


# --- main() CLI ---

def test_main_writes_reports(tmp_path: Path) -> None:
    result = ConformanceResult(
        journey="simple_rag_query",
        passed=True,
        failures=[],
        metrics={"span_count": 3},
    )
    result_json = tmp_path / "result.json"
    write_json_report(result, result_json)

    with patch.object(sys, "argv", [
        "agenteval-telemetry-report",
        "--result-json", str(result_json),
        "--output-dir", str(tmp_path / "out"),
    ]):
        main()

    assert (tmp_path / "out" / "result.report.json").exists()
    assert (tmp_path / "out" / "result.report.md").exists()


def test_main_exits_one_on_missing_result_file(tmp_path: Path) -> None:
    with patch.object(sys, "argv", [
        "agenteval-telemetry-report",
        "--result-json", str(tmp_path / "nonexistent.json"),
        "--output-dir", str(tmp_path / "out"),
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
