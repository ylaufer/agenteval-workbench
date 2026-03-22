from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from agenteval.core import service
from tests.conftest import _minimal_trace_dict


# ---------------------------------------------------------------------------
# T004: generate_case() delegates to generator
# ---------------------------------------------------------------------------


class TestGenerateCase:
    def test_delegates_to_generator_and_returns_path(
        self, repo_root_env: Path
    ) -> None:
        result = service.generate_case(
            case_id="svc_test_001",
            failure_type="tool_hallucination",
        )
        assert isinstance(result, Path)
        assert result.name == "svc_test_001"
        assert (result / "prompt.txt").exists()
        assert (result / "trace.json").exists()
        assert (result / "expected_outcome.md").exists()

    def test_raises_for_existing_case(self, repo_root_env: Path) -> None:
        service.generate_case(case_id="dup_case")
        with pytest.raises(ValueError, match="already exists"):
            service.generate_case(case_id="dup_case")

    def test_overwrite_existing_case(self, repo_root_env: Path) -> None:
        service.generate_case(case_id="ow_case")
        result = service.generate_case(case_id="ow_case", overwrite=True)
        assert result.exists()

    def test_raises_for_invalid_failure_type(self, repo_root_env: Path) -> None:
        with pytest.raises(ValueError, match="Invalid failure_type"):
            service.generate_case(case_id="bad_ft", failure_type="not_real")


# ---------------------------------------------------------------------------
# T005: validate_dataset() delegates to validator
# ---------------------------------------------------------------------------


class TestValidateDataset:
    def test_returns_validation_result(self, sample_case_dir: Path) -> None:
        result = service.validate_dataset()
        assert hasattr(result, "ok")
        assert hasattr(result, "issues")

    def test_validates_with_custom_dir(self, repo_root_env: Path) -> None:
        cases_dir = repo_root_env / "data" / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        result = service.validate_dataset(dataset_dir=cases_dir)
        assert hasattr(result, "ok")


# ---------------------------------------------------------------------------
# T006: list_cases() returns sorted case IDs
# ---------------------------------------------------------------------------


class TestListCases:
    def test_returns_sorted_list(self, repo_root_env: Path) -> None:
        cases_dir = repo_root_env / "data" / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        (cases_dir / "case_zzz").mkdir()
        (cases_dir / "case_aaa").mkdir()
        (cases_dir / "case_mmm").mkdir()

        result = service.list_cases(dataset_dir=cases_dir)
        assert result == ["case_aaa", "case_mmm", "case_zzz"]

    def test_empty_directory(self, repo_root_env: Path) -> None:
        cases_dir = repo_root_env / "data" / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        result = service.list_cases(dataset_dir=cases_dir)
        assert result == []

    def test_ignores_files(self, repo_root_env: Path) -> None:
        cases_dir = repo_root_env / "data" / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        (cases_dir / "case_001").mkdir()
        (cases_dir / "README.md").write_text("ignore me")
        result = service.list_cases(dataset_dir=cases_dir)
        assert result == ["case_001"]


# ---------------------------------------------------------------------------
# T007: load_case_metadata() returns parsed YAML header
# ---------------------------------------------------------------------------


class TestLoadCaseMetadata:
    def test_returns_header_dict(self, sample_case_dir: Path) -> None:
        result = service.load_case_metadata(sample_case_dir)
        assert isinstance(result, dict)
        assert result["case_id"] == "case_001"
        assert result["primary_failure"] == "Incomplete Execution"
        assert result["severity"] == "High"

    def test_missing_fields_return_none(self, repo_root_env: Path) -> None:
        case_dir = repo_root_env / "data" / "cases" / "sparse_case"
        case_dir.mkdir(parents=True)
        (case_dir / "expected_outcome.md").write_text(
            "---\nCase ID: sparse_case\nSeverity: Low\n---\n",
            encoding="utf-8",
        )
        result = service.load_case_metadata(case_dir)
        assert result["case_id"] == "sparse_case"
        assert result.get("primary_failure") is None


# ---------------------------------------------------------------------------
# T008: load_trace() returns trace dict
# ---------------------------------------------------------------------------


class TestLoadTrace:
    def test_returns_trace_dict(self, sample_case_dir: Path) -> None:
        result = service.load_trace(sample_case_dir)
        assert isinstance(result, dict)
        assert "steps" in result
        assert "task_id" in result


# ---------------------------------------------------------------------------
# T009: load_evaluation_template() returns None when no template
# ---------------------------------------------------------------------------


class TestLoadEvaluationTemplate:
    def test_returns_none_when_missing(self, repo_root_env: Path) -> None:
        reports_dir = repo_root_env / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        result = service.load_evaluation_template("nonexistent", reports_dir=reports_dir)
        assert result is None

    def test_returns_dict_when_present(self, repo_root_env: Path) -> None:
        reports_dir = repo_root_env / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        template_data = {"case_id": "case_001", "dimensions": {}}
        (reports_dir / "case_001.evaluation.json").write_text(
            json.dumps(template_data), encoding="utf-8"
        )
        result = service.load_evaluation_template("case_001", reports_dir=reports_dir)
        assert result is not None
        assert result["case_id"] == "case_001"


# ---------------------------------------------------------------------------
# T010: run_evaluation() calls runner.main and returns list of dicts
# ---------------------------------------------------------------------------


class TestRunEvaluation:
    def test_returns_evaluation_dicts(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        dataset_dir = repo_root / "data" / "cases"
        output_dir = repo_root / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = service.run_evaluation(
            dataset_dir=dataset_dir, output_dir=output_dir
        )
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["case_id"] == "case_001"

    def test_empty_dataset(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        output_dir = repo_root_env / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = service.run_evaluation(
            dataset_dir=dataset_dir, output_dir=output_dir
        )
        assert result == []


# ---------------------------------------------------------------------------
# T011: generate_summary_report() calls report.main and returns summary dict
# ---------------------------------------------------------------------------


class TestGenerateSummaryReport:
    def test_returns_summary_dict(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        dataset_dir = repo_root / "data" / "cases"
        output_dir = repo_root / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        # First run evaluation to create templates
        service.run_evaluation(dataset_dir=dataset_dir, output_dir=output_dir)

        result = service.generate_summary_report(
            input_dir=output_dir, output_dir=output_dir
        )
        assert isinstance(result, dict)
        assert "summary" in result
        assert "dimensions" in result

    def test_raises_when_no_templates(self, repo_root_env: Path) -> None:
        reports_dir = repo_root_env / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(RuntimeError):
            service.generate_summary_report(
                input_dir=reports_dir, output_dir=reports_dir
            )
