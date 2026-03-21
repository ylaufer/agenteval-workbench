from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pytest

from agenteval.core.calibration import (
    _collect_case_ids_from_scores_dir,
    _compute_cohens_kappa,
    _compute_percent_agreement,
    _interpret_kappa,
    compute_calibration_report,
    main,
)


Numeric = float
RubricInfo = Dict[str, Tuple[str, Numeric]]


def _default_rubric_info() -> RubricInfo:
    return {
        "accuracy": ("0-2", 1.0),
        "safety": ("0-2", 1.5),
    }


# ---------------------------------------------------------------------------
# _compute_percent_agreement
# ---------------------------------------------------------------------------


class TestComputePercentAgreement:
    def test_perfect(self) -> None:
        assert _compute_percent_agreement([1, 2, 1], [1, 2, 1]) == 1.0

    def test_none(self) -> None:
        assert _compute_percent_agreement([0, 1, 2], [2, 0, 1]) == 0.0

    def test_partial(self) -> None:
        result = _compute_percent_agreement([1, 1, 2, 2], [1, 2, 2, 0])
        assert abs(result - 0.5) < 1e-6

    def test_empty(self) -> None:
        assert _compute_percent_agreement([], []) == 0.0


# ---------------------------------------------------------------------------
# _compute_cohens_kappa
# ---------------------------------------------------------------------------


class TestComputeCohensKappa:
    def test_perfect_agreement(self) -> None:
        # All same scores → observed=1.0, expected < 1.0 → kappa=1.0
        kappa = _compute_cohens_kappa([0, 1, 2], [0, 1, 2], 0, 2)
        assert kappa is not None
        assert abs(kappa - 1.0) < 1e-6

    def test_no_data(self) -> None:
        assert _compute_cohens_kappa([], [], 0, 2) is None

    def test_all_same_category(self) -> None:
        # Both raters give 1 for everything → expected=1.0 → None
        result = _compute_cohens_kappa([1, 1, 1], [1, 1, 1], 0, 2)
        assert result is None

    def test_chance_agreement(self) -> None:
        # Some disagreement
        kappa = _compute_cohens_kappa([0, 1, 0, 1], [1, 0, 1, 0], 0, 2)
        assert kappa is not None
        assert kappa < 0.0  # Worse than chance


# ---------------------------------------------------------------------------
# _interpret_kappa
# ---------------------------------------------------------------------------


class TestInterpretKappa:
    def test_none(self) -> None:
        assert _interpret_kappa(None) == "undefined"

    def test_negative(self) -> None:
        assert _interpret_kappa(-0.1) == "poor (less than chance)"

    def test_slight(self) -> None:
        assert _interpret_kappa(0.1) == "slight"

    def test_fair(self) -> None:
        assert _interpret_kappa(0.3) == "fair"

    def test_moderate(self) -> None:
        assert _interpret_kappa(0.5) == "moderate"

    def test_substantial(self) -> None:
        assert _interpret_kappa(0.7) == "substantial"

    def test_almost_perfect(self) -> None:
        assert _interpret_kappa(0.9) == "almost perfect"

    def test_boundary_zero(self) -> None:
        assert _interpret_kappa(0.0) == "slight"

    def test_boundary_021(self) -> None:
        assert _interpret_kappa(0.21) == "fair"


# ---------------------------------------------------------------------------
# _collect_case_ids_from_scores_dir
# ---------------------------------------------------------------------------


class TestCollectCaseIds:
    def test_parses_filenames(self, tmp_path: Path) -> None:
        (tmp_path / "case_001_alice.json").touch()
        (tmp_path / "case_001_bob.json").touch()
        (tmp_path / "case_002_alice.json").touch()
        ids = _collect_case_ids_from_scores_dir(tmp_path)
        assert ids == ["case_001", "case_002"]

    def test_empty_dir(self, tmp_path: Path) -> None:
        assert _collect_case_ids_from_scores_dir(tmp_path) == []

    def test_non_json_files_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").touch()
        (tmp_path / "case_001_alice.json").touch()
        ids = _collect_case_ids_from_scores_dir(tmp_path)
        assert ids == ["case_001"]

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        assert _collect_case_ids_from_scores_dir(tmp_path / "nope") == []


# ---------------------------------------------------------------------------
# compute_calibration_report
# ---------------------------------------------------------------------------


class TestComputeCalibrationReport:
    def _write_score(
        self,
        scores_dir: Path,
        case_id: str,
        reviewer: str,
        accuracy: int,
        safety: int,
    ) -> None:
        obj = {
            "case_id": case_id,
            "reviewer_id": reviewer,
            "rubric_version": "v1_test",
            "timestamp": "2025-01-01T00:00:00Z",
            "dimensions": {
                "accuracy": {"score": accuracy},
                "safety": {"score": safety},
            },
        }
        path = scores_dir / f"{case_id}_{reviewer}.json"
        path.write_text(json.dumps(obj), encoding="utf-8")

    def test_two_reviewers_two_cases(self, repo_root_env: Path) -> None:
        scores_dir = repo_root_env / "scores"
        scores_dir.mkdir(parents=True)
        self._write_score(scores_dir, "case_001", "alice", 2, 1)
        self._write_score(scores_dir, "case_001", "bob", 2, 2)
        self._write_score(scores_dir, "case_002", "alice", 1, 1)
        self._write_score(scores_dir, "case_002", "bob", 0, 1)

        info = _default_rubric_info()
        report = compute_calibration_report(["case_001", "case_002"], scores_dir, info)
        assert report["num_cases_with_multiple_reviewers"] == 2
        assert len(report["reviewer_pairs"]) == 1
        assert report["reviewer_pairs"][0] == ["alice", "bob"]
        # Check that dimension results exist
        assert "accuracy" in report["dimensions"]
        assert "safety" in report["dimensions"]

    def test_single_reviewer_skipped(self, repo_root_env: Path) -> None:
        scores_dir = repo_root_env / "scores"
        scores_dir.mkdir(parents=True)
        self._write_score(scores_dir, "case_001", "alice", 2, 2)

        info = _default_rubric_info()
        report = compute_calibration_report(["case_001"], scores_dir, info)
        assert report["num_cases_with_multiple_reviewers"] == 0

    def test_no_scores(self, repo_root_env: Path) -> None:
        scores_dir = repo_root_env / "scores"
        scores_dir.mkdir(parents=True)
        info = _default_rubric_info()
        report = compute_calibration_report([], scores_dir, info)
        assert report["num_cases_with_multiple_reviewers"] == 0
        assert report["dimensions"] == {}


# ---------------------------------------------------------------------------
# main (CLI) — integration
# ---------------------------------------------------------------------------


class TestCalibrationMain:
    @pytest.mark.integration
    def test_generates_reports(self, repo_root_env: Path) -> None:
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"
        if not rubric_path.exists():
            pytest.skip("Real rubric not available")

        scores_dir = repo_root_env / "scores"
        scores_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = repo_root_env / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        exit_code = main(
            [
                "--scores-dir",
                str(scores_dir),
                "--rubric-path",
                str(rubric_path),
                "--output-json",
                str(reports_dir / "calibration.json"),
                "--output-md",
                str(reports_dir / "calibration.md"),
            ]
        )
        assert exit_code == 0
        assert (reports_dir / "calibration.json").exists()
        assert (reports_dir / "calibration.md").exists()
