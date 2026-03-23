from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

from agenteval.core.report import (
    _build_json_report,
    _collect_dimension_stats,
    _compute_case_overall_scores,
    _generate_recommendations,
    _inject_reviewer_scores_into_stats,
    _iter_evaluation_files,
    _parse_scale,
    _summarize_failures,
    main,
)
from agenteval.core.types import DimensionScore, ReviewerScore


Numeric = float
RubricInfo = Dict[str, Tuple[str, Numeric]]


def _default_rubric_info() -> RubricInfo:
    return {
        "accuracy": ("0-2", 1.0),
        "safety": ("0-2", 1.5),
    }


def _scored_eval(accuracy: int | None = 1, safety: int | None = 2) -> Dict[str, Any]:
    dims: Dict[str, Any] = {}
    dims["accuracy"] = {"score": accuracy, "weight": 1.0, "scale": "0-2"}
    dims["safety"] = {"score": safety, "weight": 1.5, "scale": "0-2"}
    return {
        "case_id": "case_001",
        "primary_failure": "Incomplete Execution",
        "severity": "High",
        "auto_tags": ["incomplete_execution"],
        "dimensions": dims,
    }


# ---------------------------------------------------------------------------
# _parse_scale
# ---------------------------------------------------------------------------


class TestParseScale:
    def test_zero_two(self) -> None:
        assert _parse_scale("0-2") == (0.0, 2.0)

    def test_one_five(self) -> None:
        assert _parse_scale("1-5") == (1.0, 5.0)

    def test_invalid_format_abc(self) -> None:
        with pytest.raises(ValueError, match="Unsupported scale format"):
            _parse_scale("abc")

    def test_reversed_scale(self) -> None:
        with pytest.raises(ValueError, match="Unsupported scale format"):
            _parse_scale("2-1")

    def test_single_number(self) -> None:
        with pytest.raises(ValueError, match="Unsupported scale format"):
            _parse_scale("1")

    def test_equal_values(self) -> None:
        with pytest.raises(ValueError, match="Unsupported scale format"):
            _parse_scale("2-2")


# ---------------------------------------------------------------------------
# _collect_dimension_stats
# ---------------------------------------------------------------------------


class TestCollectDimensionStats:
    def test_scored_and_unscored_mix(self) -> None:
        info = _default_rubric_info()
        evals = [_scored_eval(1, 2), _scored_eval(None, 1)]
        stats = _collect_dimension_stats(evals, info)
        assert stats["accuracy"].num_scored == 1
        assert stats["accuracy"].num_unscored == 1
        assert stats["accuracy"].mean_score == 1.0
        assert stats["safety"].num_scored == 2
        assert stats["safety"].mean_score == 1.5

    def test_empty_evaluations(self) -> None:
        info = _default_rubric_info()
        stats = _collect_dimension_stats([], info)
        for dim in stats.values():
            assert dim.num_scored == 0
            assert dim.mean_score is None

    def test_single_evaluation(self) -> None:
        info = _default_rubric_info()
        stats = _collect_dimension_stats([_scored_eval(2, 2)], info)
        assert stats["accuracy"].mean_score == 2.0
        assert stats["accuracy"].distribution == {"2": 1}


# ---------------------------------------------------------------------------
# _compute_case_overall_scores
# ---------------------------------------------------------------------------


class TestComputeCaseOverallScores:
    def test_weighted_normalized(self) -> None:
        info = _default_rubric_info()
        # accuracy=2 (max 2, weight 1.0) → normalized 1.0
        # safety=1 (max 2, weight 1.5) → normalized 0.5
        # overall = (1.0*1.0 + 0.5*1.5) / (1.0+1.5) = 1.75 / 2.5 = 0.7
        aggs = _compute_case_overall_scores([_scored_eval(2, 1)], info)
        assert len(aggs) == 1
        assert aggs[0].overall_score is not None
        assert abs(aggs[0].overall_score - 0.7) < 1e-6

    def test_all_unscored(self) -> None:
        info = _default_rubric_info()
        aggs = _compute_case_overall_scores([_scored_eval(None, None)], info)
        assert aggs[0].overall_score is None

    def test_partial_scores(self) -> None:
        info = _default_rubric_info()
        aggs = _compute_case_overall_scores([_scored_eval(2, None)], info)
        assert aggs[0].overall_score is not None
        # Only accuracy scored: normalized 1.0, weight 1.0 → overall 1.0
        assert abs(aggs[0].overall_score - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# _summarize_failures
# ---------------------------------------------------------------------------


class TestSummarizeFailures:
    def test_primary_and_severity(self) -> None:
        evals = [_scored_eval(), _scored_eval()]
        result = _summarize_failures(evals)
        assert result["primary_failure_counts"]["Incomplete Execution"] == 2
        assert result["severity_counts"]["High"] == 2
        assert result["auto_tag_counts"]["incomplete_execution"] == 2

    def test_empty(self) -> None:
        result = _summarize_failures([])
        assert result["primary_failure_counts"] == {}
        assert result["severity_counts"] == {}
        assert result["auto_tag_counts"] == {}


# ---------------------------------------------------------------------------
# _inject_reviewer_scores_into_stats
# ---------------------------------------------------------------------------


class TestInjectReviewerScores:
    def test_merges_scores(self) -> None:
        info = _default_rubric_info()
        base_stats = _collect_dimension_stats([_scored_eval(1, 2)], info)

        reviewer_scores: Dict[str, list[ReviewerScore]] = {
            "case_001": [
                ReviewerScore(
                    case_id="case_001",
                    reviewer_id="alice",
                    rubric_version="v1",
                    timestamp="t",
                    dimensions={
                        "accuracy": DimensionScore(score=2),
                        "safety": DimensionScore(score=0),
                    },
                ),
            ],
        }
        merged = _inject_reviewer_scores_into_stats(base_stats, reviewer_scores, info)
        # accuracy: was 1 (1 scored), now add 2 → mean = 1.5
        assert merged["accuracy"].num_scored == 2
        assert merged["accuracy"].mean_score is not None
        assert abs(merged["accuracy"].mean_score - 1.5) < 1e-6


# ---------------------------------------------------------------------------
# _generate_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    def test_low_score_triggers_rec(self) -> None:
        info = _default_rubric_info()
        stats = _collect_dimension_stats([_scored_eval(0, 0)], info)
        failure_summary = _summarize_failures([_scored_eval()])
        recs = _generate_recommendations(stats, failure_summary)
        assert any("accuracy" in r or "safety" in r for r in recs)

    def test_high_scores_expand_benchmark(self) -> None:
        info = _default_rubric_info()
        stats = _collect_dimension_stats([_scored_eval(2, 2)], info)
        recs = _generate_recommendations(stats, {"primary_failure_counts": {}})
        assert any("expand" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# _build_json_report
# ---------------------------------------------------------------------------


class TestBuildJsonReport:
    def test_structure(self) -> None:
        info = _default_rubric_info()
        evals = [_scored_eval()]
        stats = _collect_dimension_stats(evals, info)
        aggs = _compute_case_overall_scores(evals, info)
        failures = _summarize_failures(evals)
        report = _build_json_report(evals, stats, aggs, failures)
        assert "summary" in report
        assert "dimensions" in report
        assert "failure_summary" in report
        assert "recommendations" in report
        assert report["summary"]["num_cases"] == 1


# ---------------------------------------------------------------------------
# main (CLI) — integration
# ---------------------------------------------------------------------------


class TestReportMain:
    @pytest.mark.integration
    def test_end_to_end(self, sample_case_dir: Path, repo_root_env: Path) -> None:
        """Generate eval templates first, then run report generation."""
        from agenteval.core.runner import main as runner_main

        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"
        if not rubric_path.exists():
            pytest.skip("Real rubric not available")

        reports_dir = repo_root_env / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # First generate evaluation templates
        runner_main(
            [
                "--dataset-dir",
                str(repo_root_env / "data" / "cases"),
                "--rubric-path",
                str(rubric_path),
                "--output-dir",
                str(reports_dir),
            ]
        )

        # Now run the report
        exit_code = main(
            [
                "--input-dir",
                str(reports_dir),
                "--output-json",
                str(reports_dir / "summary.evaluation.json"),
                "--output-md",
                str(reports_dir / "summary.evaluation.md"),
                "--rubric-path",
                str(rubric_path),
                "--scores-dir",
                str(repo_root_env / "scores"),
            ]
        )
        assert exit_code == 0
        assert (reports_dir / "summary.evaluation.json").exists()
        assert (reports_dir / "summary.evaluation.md").exists()


# ---------------------------------------------------------------------------
# Auto-score aggregation tests (T025)
# ---------------------------------------------------------------------------


def _auto_eval(
    case_id: str = "case_001",
    accuracy: int | None = 2,
    safety: int | None = 1,
) -> Dict[str, Any]:
    """Build an auto-evaluation dict with _scoring_source tag."""
    dims: Dict[str, Any] = {}
    dims["accuracy"] = {"score": accuracy, "weight": 1.0, "scale": "0-2"}
    dims["safety"] = {"score": safety, "weight": 1.5, "scale": "0-2"}
    return {
        "case_id": case_id,
        "scoring_type": "auto",
        "dimensions": dims,
        "auto_tags": [],
        "_scoring_source": "auto",
    }


class TestAutoScoreAggregation:
    def test_combined_report_includes_both(self) -> None:
        """Combined report aggregates manual and auto evaluations."""
        info = _default_rubric_info()
        manual = _scored_eval(1, 2)
        manual["_scoring_source"] = "manual"
        auto = _auto_eval("case_002", 2, 1)

        evals = [manual, auto]
        stats = _collect_dimension_stats(evals, info)
        aggs = _compute_case_overall_scores(evals, info)
        failures = _summarize_failures(evals)
        report = _build_json_report(evals, stats, aggs, failures)

        assert report["summary"]["num_cases"] == 2
        assert report["summary"]["num_auto_scored"] == 1
        assert report["summary"]["num_manual_scored"] == 1

    def test_source_attribution_in_failed_cases(self) -> None:
        """Failed case entries include scoring_source field."""
        info = _default_rubric_info()
        auto = _auto_eval("case_001", 0, 0)

        evals = [auto]
        stats = _collect_dimension_stats(evals, info)
        aggs = _compute_case_overall_scores(evals, info)
        failures = _summarize_failures(evals)
        report = _build_json_report(evals, stats, aggs, failures)

        assert len(report["failed_cases"]) == 1
        assert report["failed_cases"][0]["scoring_source"] == "auto"

    def test_iter_evaluation_files_manual_only(self, tmp_path: Path) -> None:
        """Scoring type 'manual' excludes auto evaluation files."""
        import json as _json

        (tmp_path / "case_001.evaluation.json").write_text(
            _json.dumps({"case_id": "case_001"}), encoding="utf-8"
        )
        (tmp_path / "case_002.auto_evaluation.json").write_text(
            _json.dumps({"case_id": "case_002"}), encoding="utf-8"
        )

        files = list(_iter_evaluation_files(tmp_path, scoring_type="manual"))
        assert len(files) == 1
        assert files[0].name == "case_001.evaluation.json"

    def test_iter_evaluation_files_auto_only(self, tmp_path: Path) -> None:
        """Scoring type 'auto' excludes manual evaluation files."""
        import json as _json

        (tmp_path / "case_001.evaluation.json").write_text(
            _json.dumps({"case_id": "case_001"}), encoding="utf-8"
        )
        (tmp_path / "case_002.auto_evaluation.json").write_text(
            _json.dumps({"case_id": "case_002"}), encoding="utf-8"
        )

        files = list(_iter_evaluation_files(tmp_path, scoring_type="auto"))
        assert len(files) == 1
        assert files[0].name == "case_002.auto_evaluation.json"

    def test_iter_evaluation_files_combined(self, tmp_path: Path) -> None:
        """Scoring type 'combined' includes both."""
        import json as _json

        (tmp_path / "case_001.evaluation.json").write_text(
            _json.dumps({"case_id": "case_001"}), encoding="utf-8"
        )
        (tmp_path / "case_002.auto_evaluation.json").write_text(
            _json.dumps({"case_id": "case_002"}), encoding="utf-8"
        )

        files = list(_iter_evaluation_files(tmp_path, scoring_type="combined"))
        assert len(files) == 2
