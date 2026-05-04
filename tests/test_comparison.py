"""Tests for the run comparison engine."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pytest

from agenteval.core.comparison import (
    CaseDelta,
    ComparisonResult,
    ComparisonSummary,
    DimensionDelta,
    _build_case_deltas,
    _build_dimension_deltas,
    _build_summary,
    _compute_overall_score,
    _normalize_score,
    _parse_scale_max,
    classify_change,
    compare_runs,
    main,
)


# ---------------------------------------------------------------------------
# T006 + T007: Unit tests — classify_change, scale helpers, overall score
# ---------------------------------------------------------------------------


class TestParseScaleMax:
    def test_standard_scale(self) -> None:
        assert _parse_scale_max("0-2") == 2.0

    def test_wider_scale(self) -> None:
        assert _parse_scale_max("0-5") == 5.0

    def test_fallback_on_bad_format(self) -> None:
        assert _parse_scale_max("invalid") == 2.0

    def test_fallback_on_empty(self) -> None:
        assert _parse_scale_max("") == 2.0


class TestNormalizeScore:
    def test_max_score(self) -> None:
        assert _normalize_score(2, 2.0) == 1.0

    def test_zero_score(self) -> None:
        assert _normalize_score(0, 2.0) == 0.0

    def test_mid_score(self) -> None:
        assert _normalize_score(1, 2.0) == 0.5

    def test_zero_scale_max(self) -> None:
        assert _normalize_score(2, 0.0) == 0.0


class TestComputeOverallScore:
    def test_all_scored(self) -> None:
        dims = {
            "accuracy": {"score": 2, "weight": 1.0, "scale": "0-2"},
            "tool_use": {"score": 1, "weight": 1.0, "scale": "0-2"},
        }
        score = _compute_overall_score(dims)
        assert score == pytest.approx(0.75)

    def test_all_null(self) -> None:
        dims = {
            "accuracy": {"score": None, "weight": 1.0, "scale": "0-2"},
        }
        assert _compute_overall_score(dims) is None

    def test_partial_null(self) -> None:
        dims = {
            "accuracy": {"score": 2, "weight": 1.0, "scale": "0-2"},
            "tool_use": {"score": None, "weight": 1.0, "scale": "0-2"},
        }
        # Only accuracy scored: 2/2 = 1.0
        assert _compute_overall_score(dims) == pytest.approx(1.0)

    def test_weighted(self) -> None:
        dims = {
            "accuracy": {"score": 2, "weight": 1.0, "scale": "0-2"},       # norm=1.0
            "security_safety": {"score": 0, "weight": 1.5, "scale": "0-2"}, # norm=0.0
        }
        # weighted: (1.0*1.0 + 0.0*1.5) / (1.0+1.5) = 1.0/2.5 = 0.4
        assert _compute_overall_score(dims) == pytest.approx(0.4)

    def test_empty_dimensions(self) -> None:
        assert _compute_overall_score({}) is None


class TestClassifyChange:
    def test_improved(self) -> None:
        assert classify_change(0.5, 0.8) == "improved"

    def test_regressed(self) -> None:
        assert classify_change(0.8, 0.5) == "regressed"

    def test_unchanged_equal(self) -> None:
        assert classify_change(0.5, 0.5) == "unchanged"

    def test_both_none(self) -> None:
        assert classify_change(None, None) == "unchanged"

    def test_a_none(self) -> None:
        assert classify_change(None, 0.5) == "unchanged"

    def test_b_none(self) -> None:
        assert classify_change(0.5, None) == "unchanged"

    def test_tiny_positive_delta(self) -> None:
        assert classify_change(0.5, 0.500001) == "improved"

    def test_tiny_negative_delta(self) -> None:
        assert classify_change(0.500001, 0.5) == "regressed"


# ---------------------------------------------------------------------------
# T012: Integration test — compare two real run directories
# ---------------------------------------------------------------------------


REAL_RUN_A = "20260325T184347_ee91"
REAL_RUN_B = "20260325T184409_b550"


def _real_runs_available() -> bool:
    from agenteval.core.runs import get_run
    return get_run(REAL_RUN_A) is not None and get_run(REAL_RUN_B) is not None


@pytest.mark.skipif(not _real_runs_available(), reason="Real run directories not available")
def test_compare_real_runs_returns_result() -> None:
    result = compare_runs(REAL_RUN_A, REAL_RUN_B)
    assert isinstance(result, ComparisonResult)
    assert result.run_a == REAL_RUN_A
    assert result.run_b == REAL_RUN_B
    assert result.summary.total_cases_compared >= 0
    assert result.summary.net_quality_change in (
        "improved", "regressed", "unchanged", "insufficient_data"
    )


@pytest.mark.skipif(not _real_runs_available(), reason="Real run directories not available")
def test_compare_real_runs_schema_valid() -> None:
    import jsonschema
    result = compare_runs(REAL_RUN_A, REAL_RUN_B)
    from agenteval.dataset.validator import _get_repo_root
    schema_path = _get_repo_root() / "schemas" / "comparison_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=asdict(result), schema=schema)


@pytest.mark.skipif(not _real_runs_available(), reason="Real run directories not available")
def test_compare_real_runs_case_deltas_populated() -> None:
    result = compare_runs(REAL_RUN_A, REAL_RUN_B)
    assert len(result.case_deltas) > 0
    for cd in result.case_deltas:
        assert cd.status in ("improved", "regressed", "unchanged", "new", "removed")


# ---------------------------------------------------------------------------
# T013: Edge case tests
# ---------------------------------------------------------------------------


def test_compare_missing_run_a_raises() -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        compare_runs("nonexistent_run_a", "nonexistent_run_b")


def test_compare_missing_run_b_raises(tmp_path: Path) -> None:
    # Create a fake run_a directory with a run.json
    from agenteval.dataset.validator import _get_repo_root
    repo_root = _get_repo_root()
    run_id = "test_fake_run_a_xyz"
    run_dir = repo_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(
        json.dumps({
            "run_id": run_id, "status": "completed", "started_at": "2026-01-01T00:00:00+00:00",
            "dataset_dir": str(repo_root / "data" / "cases"),
            "rubric_path": str(repo_root / "rubrics" / "v1_agent_general.json"),
            "num_cases": 0,
        }),
        encoding="utf-8",
    )
    try:
        with pytest.raises(FileNotFoundError, match="not found"):
            compare_runs(run_id, "nonexistent_run_b_xyz")
    finally:
        import shutil
        shutil.rmtree(run_dir, ignore_errors=True)


def test_disjoint_case_sets_new_removed() -> None:
    results_a = [
        {"case_id": "case_001", "primary_failure": "X", "dimensions": {
            "accuracy": {"score": 1, "weight": 1.0, "scale": "0-2"},
        }},
    ]
    results_b = [
        {"case_id": "case_002", "primary_failure": "Y", "dimensions": {
            "accuracy": {"score": 2, "weight": 1.0, "scale": "0-2"},
        }},
    ]
    deltas = _build_case_deltas(results_a, results_b)
    statuses = {cd.case_id: cd.status for cd in deltas}
    assert statuses["case_001"] == "removed"
    assert statuses["case_002"] == "new"


def test_all_null_scores_insufficient_data() -> None:
    results_a = [
        {"case_id": "case_001", "dimensions": {"accuracy": {"score": None, "weight": 1.0, "scale": "0-2"}}},
    ]
    results_b = [
        {"case_id": "case_001", "dimensions": {"accuracy": {"score": None, "weight": 1.0, "scale": "0-2"}}},
    ]
    deltas = _build_case_deltas(results_a, results_b)
    summary = _build_summary(deltas, "a", "b")
    assert summary.net_quality_change == "insufficient_data"
    assert summary.overall_score_delta is None


def test_build_summary_counts() -> None:
    deltas = [
        CaseDelta("c1", "improved", overall_score_a=0.5, overall_score_b=0.8, overall_delta=0.3),
        CaseDelta("c2", "regressed", overall_score_a=0.8, overall_score_b=0.5, overall_delta=-0.3),
        CaseDelta("c3", "unchanged", overall_score_a=0.5, overall_score_b=0.5, overall_delta=0.0),
        CaseDelta("c4", "new", overall_score_b=0.7),
        CaseDelta("c5", "removed", overall_score_a=0.6),
    ]
    summary = _build_summary(deltas, "a", "b")
    assert summary.total_cases_compared == 3
    assert summary.cases_improved == 1
    assert summary.cases_regressed == 1
    assert summary.cases_unchanged == 1
    assert summary.cases_new == 1
    assert summary.cases_removed == 1


def test_failure_type_analysis() -> None:
    deltas = [
        CaseDelta("c1", "unchanged", primary_failure_a="TypeA", primary_failure_b="TypeB"),
        CaseDelta("c2", "improved", primary_failure_a="TypeA", primary_failure_b="TypeA"),
    ]
    summary = _build_summary(deltas, "a", "b")
    assert "TypeB" in summary.new_failure_types
    assert "TypeA" not in summary.new_failure_types  # still present in B
    assert "TypeA" not in summary.resolved_failure_types  # still present


def test_dimension_deltas_improved_regressed_counts() -> None:
    deltas = [
        CaseDelta("c1", "improved", dimension_deltas={"accuracy": 0.3, "tool_use": -0.1}),
        CaseDelta("c2", "regressed", dimension_deltas={"accuracy": -0.2, "tool_use": 0.0}),
        CaseDelta("c3", "new"),
    ]
    dim_deltas = _build_dimension_deltas(deltas)
    acc = next(d for d in dim_deltas if d.dimension == "accuracy")
    tool = next(d for d in dim_deltas if d.dimension == "tool_use")
    assert acc.cases_improved == 1
    assert acc.cases_regressed == 1
    assert tool.cases_regressed == 1
    assert tool.cases_unchanged == 1


# ---------------------------------------------------------------------------
# T015: CLI tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _real_runs_available(), reason="Real run directories not available")
def test_cli_valid_runs_exits_zero() -> None:
    with patch.object(sys, "argv", [
        "agenteval-compare", "--run-a", REAL_RUN_A, "--run-b", REAL_RUN_B,
    ]):
        exit_code = main()
    assert exit_code == 0


def test_cli_missing_run_exits_one() -> None:
    exit_code = main(["--run-a", "nonexistent_xyz", "--run-b", "also_nonexistent_xyz"])
    assert exit_code == 1


def test_cli_no_args_exits_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


@pytest.mark.skipif(not _real_runs_available(), reason="Real run directories not available")
def test_cli_output_json_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "comparison.json"
    exit_code = main([
        "--run-a", REAL_RUN_A,
        "--run-b", REAL_RUN_B,
        "--output-json", str(out),
    ])
    assert exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "comparison_id" in data
    assert "summary" in data


@pytest.mark.skipif(not _real_runs_available(), reason="Real run directories not available")
def test_cli_baseline_current_aliases() -> None:
    exit_code = main(["--baseline", REAL_RUN_A, "--current", REAL_RUN_B])
    assert exit_code == 0
