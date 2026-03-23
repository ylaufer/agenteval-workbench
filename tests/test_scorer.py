"""Tests for the auto-scoring orchestrator and registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agenteval.core.evaluators import EvaluatorRegistry
from agenteval.core.evaluators.base import Evaluator
from agenteval.core.scorer import default_registry, main as scorer_main, score_case, score_dataset
from agenteval.core.types import DimensionScoreResult, RubricDimension
from agenteval.core.loader import load_rubric
from tests.conftest import _minimal_trace_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubEvaluator:
    """A simple evaluator that always returns score=2."""

    def __init__(self, dim_name: str = "accuracy") -> None:
        self._dim_name = dim_name

    @property
    def dimension_name(self) -> str:
        return self._dim_name

    def score_dimension(
        self,
        trace: dict[str, Any],
        rubric_dimension: RubricDimension,
    ) -> DimensionScoreResult:
        return DimensionScoreResult(
            dimension_name=self._dim_name,
            score=2,
            weight=rubric_dimension.weight,
            scale=rubric_dimension.scale,
            evidence_step_ids=("s1",),
            notes="Stub evaluator: always 2.",
            evaluator_type="rule",
        )


class _FailingEvaluator:
    """An evaluator that always raises."""

    @property
    def dimension_name(self) -> str:
        return "accuracy"

    def score_dimension(
        self,
        trace: dict[str, Any],
        rubric_dimension: RubricDimension,
    ) -> DimensionScoreResult:
        msg = "deliberate failure"
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# EvaluatorRegistry tests
# ---------------------------------------------------------------------------


class TestEvaluatorRegistry:
    def test_register_and_get(self) -> None:
        reg = EvaluatorRegistry()
        ev = _StubEvaluator("accuracy")
        reg.register(ev)
        assert reg.get("accuracy") is ev
        assert reg.get("missing") is None

    def test_registered_dimensions(self) -> None:
        reg = EvaluatorRegistry()
        reg.register(_StubEvaluator("accuracy"))
        reg.register(_StubEvaluator("safety"))
        assert sorted(reg.registered_dimensions()) == ["accuracy", "safety"]

    def test_score_all_returns_results(self, repo_root_env: Path) -> None:
        rubric = load_rubric(
            rubric_path=repo_root_env / "rubrics" / "v1_agent_general.json"
        )
        reg = EvaluatorRegistry()
        reg.register(_StubEvaluator("accuracy"))

        trace = _minimal_trace_dict()
        results = reg.score_all(trace, rubric)
        assert "accuracy" in results
        assert results["accuracy"].score == 2

    def test_score_all_isolates_errors(self, repo_root_env: Path) -> None:
        rubric = load_rubric(
            rubric_path=repo_root_env / "rubrics" / "v1_agent_general.json"
        )
        reg = EvaluatorRegistry()
        reg.register(_FailingEvaluator())

        trace = _minimal_trace_dict()
        results = reg.score_all(trace, rubric)
        assert "accuracy" in results
        assert results["accuracy"].score is None
        assert results["accuracy"].error == "deliberate failure"

    def test_overwrite_evaluator(self) -> None:
        reg = EvaluatorRegistry()
        ev1 = _StubEvaluator("accuracy")
        ev2 = _StubEvaluator("accuracy")
        reg.register(ev1)
        reg.register(ev2)
        assert reg.get("accuracy") is ev2


# ---------------------------------------------------------------------------
# score_case tests
# ---------------------------------------------------------------------------


class TestScoreCase:
    def test_returns_auto_evaluation_dict(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        rubric = load_rubric(
            rubric_path=repo_root / "rubrics" / "v1_agent_general.json"
        )
        reg = EvaluatorRegistry()
        reg.register(_StubEvaluator("accuracy"))

        result = score_case(sample_case_dir, rubric, reg)
        assert result["case_id"] == "case_001"
        assert result["scoring_type"] == "auto"
        assert "accuracy" in result["dimensions"]
        assert result["dimensions"]["accuracy"]["score"] == 2

    def test_unregistered_dimensions_included(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        rubric = load_rubric(
            rubric_path=repo_root / "rubrics" / "v1_agent_general.json"
        )
        reg = EvaluatorRegistry()  # empty — no evaluators

        result = score_case(sample_case_dir, rubric, reg)
        # All 6 dimensions should be present with score=None
        for dim_name, dim_data in result["dimensions"].items():
            assert dim_data["score"] is None
            assert dim_data["error"] == "no_evaluator"

    def test_metadata_has_timestamp(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        rubric = load_rubric(
            rubric_path=repo_root / "rubrics" / "v1_agent_general.json"
        )
        result = score_case(sample_case_dir, rubric, EvaluatorRegistry())
        assert "timestamp" in result["metadata"]


# ---------------------------------------------------------------------------
# score_dataset tests
# ---------------------------------------------------------------------------


class TestScoreDataset:
    def test_writes_output_files(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        dataset_dir = repo_root / "data" / "cases"
        output_dir = repo_root / "auto_reports"

        reg = EvaluatorRegistry()
        reg.register(_StubEvaluator("accuracy"))

        results = score_dataset(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            registry=reg,
        )
        assert len(results) >= 1
        out_file = output_dir / "case_001.auto_evaluation.json"
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["case_id"] == "case_001"
        assert data["scoring_type"] == "auto"

    def test_empty_dataset(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        output_dir = repo_root_env / "auto_reports"

        results = score_dataset(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
        )
        assert results == []

    def test_schema_validation(self, sample_case_dir: Path) -> None:
        """Verify output passes JSON schema validation."""
        import jsonschema

        repo_root = sample_case_dir.parent.parent.parent
        dataset_dir = repo_root / "data" / "cases"
        output_dir = repo_root / "auto_reports"

        reg = EvaluatorRegistry()
        reg.register(_StubEvaluator("accuracy"))
        results = score_dataset(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            registry=reg,
        )

        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "auto_evaluation_schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        for result in results:
            jsonschema.validate(result, schema)


# ---------------------------------------------------------------------------
# default_registry tests
# ---------------------------------------------------------------------------


class TestDefaultRegistry:
    def test_has_built_in_evaluators(self) -> None:
        reg = default_registry()
        dims = reg.registered_dimensions()
        assert "tool_use" in dims
        assert "security_safety" in dims


# ---------------------------------------------------------------------------
# CLI entry point tests (T028)
# ---------------------------------------------------------------------------


class TestCLIMain:
    def test_exit_0_on_success(self, sample_case_dir: Path) -> None:
        repo_root = sample_case_dir.parent.parent.parent
        output_dir = repo_root / "auto_reports_cli"
        exit_code = scorer_main([
            "--dataset-dir", str(repo_root / "data" / "cases"),
            "--output-dir", str(output_dir),
        ])
        assert exit_code == 0
        # At least one output file should exist
        auto_files = list(output_dir.glob("*.auto_evaluation.json"))
        assert len(auto_files) >= 1

    def test_exit_2_invalid_dataset_dir(self, repo_root_env: Path) -> None:
        exit_code = scorer_main([
            "--dataset-dir", str(repo_root_env / "nonexistent_dir"),
            "--output-dir", str(repo_root_env / "auto_reports_cli"),
        ])
        assert exit_code == 2

    def test_default_strategy_is_rule(self, sample_case_dir: Path) -> None:
        """Default strategy should produce rule-based scores."""
        repo_root = sample_case_dir.parent.parent.parent
        output_dir = repo_root / "auto_reports_cli2"
        exit_code = scorer_main([
            "--dataset-dir", str(repo_root / "data" / "cases"),
            "--output-dir", str(output_dir),
            "--strategy", "rule",
        ])
        assert exit_code == 0
