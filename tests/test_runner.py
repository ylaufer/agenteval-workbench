from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agenteval.core.runner import (
    _build_case_template,
    _parse_expected_outcome_header,
    _summarize_trace,
    _write_json_template,
    _write_markdown_template,
    main,
)
from agenteval.core.loader import _rubric_from_dict
from tests.conftest import _minimal_rubric_dict, _minimal_trace_dict


# ---------------------------------------------------------------------------
# _parse_expected_outcome_header
# ---------------------------------------------------------------------------


class TestParseExpectedOutcomeHeader:
    def test_full_header(self, tmp_path: Path) -> None:
        path = tmp_path / "expected_outcome.md"
        path.write_text(
            "---\nCase ID: case_001\nPrimary Failure: Incomplete Execution\n"
            "Secondary Failures: Hallucination, Format Violation\n"
            "Severity: High\n---\n\nBody text.\n",
            encoding="utf-8",
        )
        header = _parse_expected_outcome_header(path)
        assert header.case_id == "case_001"
        assert header.primary_failure == "Incomplete Execution"
        assert header.secondary_failures == ("Hallucination", "Format Violation")
        assert header.severity == "High"

    def test_partial_header(self, tmp_path: Path) -> None:
        path = tmp_path / "expected_outcome.md"
        path.write_text(
            "---\nCase ID: case_002\nSeverity: Low\n---\n",
            encoding="utf-8",
        )
        header = _parse_expected_outcome_header(path)
        assert header.case_id == "case_002"
        assert header.primary_failure is None
        assert header.secondary_failures == ()
        assert header.severity == "Low"

    def test_no_header_block(self, tmp_path: Path) -> None:
        path = tmp_path / "expected_outcome.md"
        path.write_text("Just some text without a header.\n", encoding="utf-8")
        header = _parse_expected_outcome_header(path)
        assert header.case_id is None
        assert header.primary_failure is None

    def test_missing_closing_delimiter(self, tmp_path: Path) -> None:
        path = tmp_path / "expected_outcome.md"
        path.write_text(
            "---\nCase ID: case_003\nPrimary Failure: X\n\nBody text\n",
            encoding="utf-8",
        )
        header = _parse_expected_outcome_header(path)
        # Should still parse what it can before hitting non-header lines
        assert header.case_id == "case_003"
        assert header.primary_failure == "X"


# ---------------------------------------------------------------------------
# _summarize_trace
# ---------------------------------------------------------------------------


class TestSummarizeTrace:
    def test_counts_step_types(self, minimal_trace: Dict[str, Any]) -> None:
        summary = _summarize_trace(minimal_trace)
        assert summary["num_steps"] == 4
        assert summary["type_counts"]["thought"] == 1
        assert summary["type_counts"]["tool_call"] == 1
        assert summary["type_counts"]["observation"] == 1
        assert summary["type_counts"]["final_answer"] == 1

    def test_extracts_metadata(self, minimal_trace: Dict[str, Any]) -> None:
        summary = _summarize_trace(minimal_trace)
        assert summary["run_timestamp"] == "2025-01-15T10:30:00Z"
        assert summary["run_latency_ms"] == 1500

    def test_empty_steps(self) -> None:
        trace: Dict[str, Any] = {"steps": [], "metadata": {}}
        summary = _summarize_trace(trace)
        assert summary["num_steps"] == 0
        assert summary["type_counts"] == {}

    def test_non_list_steps(self) -> None:
        trace: Dict[str, Any] = {"steps": "bad", "metadata": {}}
        summary = _summarize_trace(trace)
        assert summary["num_steps"] == 0


# ---------------------------------------------------------------------------
# _build_case_template
# ---------------------------------------------------------------------------


class TestBuildCaseTemplate:
    def test_all_fields(self, minimal_trace: Dict[str, Any]) -> None:
        rubric = _rubric_from_dict(_minimal_rubric_dict())
        header = (
            _parse_expected_outcome_header.__wrapped__
            if hasattr(_parse_expected_outcome_header, "__wrapped__")
            else None
        )

        # Use a real header object
        from agenteval.core.runner import _ExpectedOutcomeHeader

        header = _ExpectedOutcomeHeader(
            case_id="case_001",
            primary_failure="Incomplete Execution",
            secondary_failures=("Hallucination",),
            severity="High",
        )
        template = _build_case_template("case_001", minimal_trace, rubric, header)
        assert template.case_id == "case_001"
        assert template.rubric_version == "v1_test"
        assert "accuracy" in template.dimensions
        assert "safety" in template.dimensions
        assert template.primary_failure == "Incomplete Execution"
        assert "primary:Incomplete Execution" in template.labels
        assert "severity:High" in template.labels

    def test_auto_tags_propagated(self, minimal_trace: Dict[str, Any]) -> None:
        rubric = _rubric_from_dict(_minimal_rubric_dict())
        from agenteval.core.runner import _ExpectedOutcomeHeader

        header = _ExpectedOutcomeHeader(
            case_id=None,
            primary_failure=None,
            secondary_failures=(),
            severity=None,
        )
        template = _build_case_template("case_001", minimal_trace, rubric, header)
        # auto_tags is a tuple (may or may not have tags depending on trace content)
        assert isinstance(template.auto_tags, tuple)


# ---------------------------------------------------------------------------
# _write_json_template / _write_markdown_template
# ---------------------------------------------------------------------------


class TestWriteTemplates:
    def _make_template(self) -> Any:
        rubric = _rubric_from_dict(_minimal_rubric_dict())
        trace = _minimal_trace_dict()
        from agenteval.core.runner import _ExpectedOutcomeHeader

        header = _ExpectedOutcomeHeader(
            case_id="case_001",
            primary_failure="Test Failure",
            secondary_failures=(),
            severity="Low",
        )
        return _build_case_template("case_001", trace, rubric, header), rubric

    def test_json_output(self, tmp_path: Path) -> None:
        template, _ = self._make_template()
        out = tmp_path / "test.evaluation.json"
        _write_json_template(out, template)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["case_id"] == "case_001"
        assert "accuracy" in data["dimensions"]

    def test_markdown_output(self, tmp_path: Path) -> None:
        template, rubric = self._make_template()
        out = tmp_path / "test.evaluation.md"
        _write_markdown_template(out, template, rubric)
        text = out.read_text(encoding="utf-8")
        assert "Case case_001" in text
        assert "`accuracy`" in text
        assert "Rubric version" in text


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


class TestRunnerMain:
    @pytest.mark.integration
    def test_end_to_end(self, sample_case_dir: Path, repo_root_env: Path) -> None:
        output_dir = repo_root_env / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use real rubric from the repo
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"
        if not rubric_path.exists():
            pytest.skip("Real rubric not available")

        exit_code = main(
            [
                "--dataset-dir",
                str(repo_root_env / "data" / "cases"),
                "--rubric-path",
                str(rubric_path),
                "--output-dir",
                str(output_dir),
            ]
        )
        assert exit_code == 0

        # Check outputs were generated
        json_files = list(output_dir.glob("*.evaluation.json"))
        md_files = list(output_dir.glob("*.evaluation.md"))
        assert len(json_files) >= 1
        assert len(md_files) >= 1
