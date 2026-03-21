from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agenteval.core.loader import (
    _rubric_from_dict,
    _reviewer_score_from_dict,
    load_rubric,
    load_trace,
    load_reviewer_score,
    load_reviewer_scores_for_case,
)
from agenteval.core.types import ReviewerScore, Rubric


# ---------------------------------------------------------------------------
# load_rubric
# ---------------------------------------------------------------------------


class TestLoadRubric:
    def test_valid(self, repo_root_env: Path, minimal_rubric_dict: Dict[str, Any]) -> None:
        rubric_path = repo_root_env / "rubrics" / "test_rubric.json"
        rubric_path.write_text(json.dumps(minimal_rubric_dict), encoding="utf-8")
        schema_path = repo_root_env / "schemas" / "rubric_schema.json"
        rubric = load_rubric(rubric_path=rubric_path, schema_path=schema_path)
        assert isinstance(rubric, Rubric)
        assert rubric.version == "v1_test"
        assert len(rubric.dimensions) == 2

    def test_schema_validation_failure(self, repo_root_env: Path) -> None:
        rubric_path = repo_root_env / "rubrics" / "bad_rubric.json"
        rubric_path.write_text(json.dumps({"version": "v1"}), encoding="utf-8")
        schema_path = repo_root_env / "schemas" / "rubric_schema.json"
        with pytest.raises(Exception):
            load_rubric(rubric_path=rubric_path, schema_path=schema_path)

    def test_non_dict_rubric(self, repo_root_env: Path) -> None:
        rubric_path = repo_root_env / "rubrics" / "list_rubric.json"
        rubric_path.write_text("[1, 2, 3]", encoding="utf-8")
        schema_path = repo_root_env / "schemas" / "rubric_schema.json"
        with pytest.raises((TypeError, Exception)):
            load_rubric(rubric_path=rubric_path, schema_path=schema_path)


# ---------------------------------------------------------------------------
# _rubric_from_dict
# ---------------------------------------------------------------------------


class TestRubricFromDict:
    def test_full(self, minimal_rubric_dict: Dict[str, Any]) -> None:
        rubric = _rubric_from_dict(minimal_rubric_dict)
        assert rubric.version == "v1_test"
        assert rubric.name == "Test Rubric"
        assert len(rubric.dimensions) == 2
        assert rubric.security_redact_patterns == ("sk-[A-Za-z0-9]+",)

    def test_no_security(self, minimal_rubric_dict: Dict[str, Any]) -> None:
        del minimal_rubric_dict["security"]
        rubric = _rubric_from_dict(minimal_rubric_dict)
        assert rubric.security_redact_patterns == ()

    def test_no_name(self, minimal_rubric_dict: Dict[str, Any]) -> None:
        del minimal_rubric_dict["name"]
        rubric = _rubric_from_dict(minimal_rubric_dict)
        assert rubric.name is None

    def test_bad_dimensions_type(self, minimal_rubric_dict: Dict[str, Any]) -> None:
        minimal_rubric_dict["dimensions"] = "not a list"
        with pytest.raises(TypeError, match="dimensions must be a list"):
            _rubric_from_dict(minimal_rubric_dict)

    def test_non_dict_dimension(self, minimal_rubric_dict: Dict[str, Any]) -> None:
        minimal_rubric_dict["dimensions"] = ["not a dict"]
        with pytest.raises(TypeError, match="each dimension must be an object"):
            _rubric_from_dict(minimal_rubric_dict)

    def test_default_weight(self, minimal_rubric_dict: Dict[str, Any]) -> None:
        del minimal_rubric_dict["dimensions"][0]["weight"]
        rubric = _rubric_from_dict(minimal_rubric_dict)
        assert rubric.dimensions[0].weight == 1.0


# ---------------------------------------------------------------------------
# load_trace
# ---------------------------------------------------------------------------


class TestLoadTrace:
    def test_valid(self, repo_root_env: Path, minimal_trace: Dict[str, Any]) -> None:
        trace_path = repo_root_env / "traces" / "trace.json"
        trace_path.parent.mkdir(parents=True)
        trace_path.write_text(json.dumps(minimal_trace), encoding="utf-8")
        result = load_trace(trace_path)
        assert result["task_id"] == "task_001"

    def test_schema_failure(self, repo_root_env: Path) -> None:
        trace_path = repo_root_env / "traces" / "bad.json"
        trace_path.parent.mkdir(parents=True)
        trace_path.write_text('{"task_id": "x"}', encoding="utf-8")
        with pytest.raises(Exception):
            load_trace(trace_path)

    def test_non_dict_trace(self, repo_root_env: Path) -> None:
        trace_path = repo_root_env / "traces" / "list.json"
        trace_path.parent.mkdir(parents=True)
        trace_path.write_text("[1,2,3]", encoding="utf-8")
        with pytest.raises(Exception):
            load_trace(trace_path)


# ---------------------------------------------------------------------------
# load_reviewer_score / _reviewer_score_from_dict
# ---------------------------------------------------------------------------


class TestLoadReviewerScore:
    def test_valid(
        self,
        repo_root_env: Path,
        sample_reviewer_score_dict: Dict[str, Any],
    ) -> None:
        score_path = repo_root_env / "scores" / "case_001_alice.json"
        score_path.parent.mkdir(parents=True)
        score_path.write_text(json.dumps(sample_reviewer_score_dict), encoding="utf-8")
        rs = load_reviewer_score(score_path)
        assert isinstance(rs, ReviewerScore)
        assert rs.case_id == "case_001"
        assert rs.reviewer_id == "alice"
        assert rs.dimensions["accuracy"].score == 2

    def test_schema_failure_uppercase_reviewer(self, repo_root_env: Path) -> None:
        bad = {
            "case_id": "case_001",
            "reviewer_id": "Alice",  # uppercase violates schema pattern
            "rubric_version": "v1",
            "timestamp": "2025-01-01",
            "dimensions": {"accuracy": {"score": 1}},
        }
        score_path = repo_root_env / "scores" / "case_001_Alice.json"
        score_path.parent.mkdir(parents=True)
        score_path.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(Exception):
            load_reviewer_score(score_path)


class TestReviewerScoreFromDict:
    def test_full(self, sample_reviewer_score_dict: Dict[str, Any]) -> None:
        rs = _reviewer_score_from_dict(sample_reviewer_score_dict)
        assert rs.case_id == "case_001"
        assert rs.overall_notes == "Decent evaluation"
        assert rs.dimensions["safety"].notes == "Minor issue"

    def test_missing_optional_notes(self) -> None:
        obj = {
            "case_id": "c1",
            "reviewer_id": "bob",
            "rubric_version": "v1",
            "timestamp": "t",
            "dimensions": {"accuracy": {"score": 0}},
        }
        rs = _reviewer_score_from_dict(obj)
        assert rs.dimensions["accuracy"].notes == ""
        assert rs.overall_notes == ""

    def test_empty_dimensions(self) -> None:
        obj = {
            "case_id": "c1",
            "reviewer_id": "bob",
            "rubric_version": "v1",
            "timestamp": "t",
        }
        rs = _reviewer_score_from_dict(obj)
        assert rs.dimensions == {}


# ---------------------------------------------------------------------------
# load_reviewer_scores_for_case
# ---------------------------------------------------------------------------


class TestLoadReviewerScoresForCase:
    def test_multiple_scores(
        self,
        repo_root_env: Path,
        sample_reviewer_score_dict: Dict[str, Any],
    ) -> None:
        scores_dir = repo_root_env / "scores"
        scores_dir.mkdir(parents=True)
        for reviewer in ("alice", "bob"):
            d = dict(sample_reviewer_score_dict)
            d["reviewer_id"] = reviewer
            path = scores_dir / f"case_001_{reviewer}.json"
            path.write_text(json.dumps(d), encoding="utf-8")
        result = load_reviewer_scores_for_case("case_001", scores_dir)
        assert len(result) == 2

    def test_no_scores(self, repo_root_env: Path) -> None:
        scores_dir = repo_root_env / "scores"
        scores_dir.mkdir(parents=True)
        result = load_reviewer_scores_for_case("case_999", scores_dir)
        assert result == []

    def test_missing_dir(self, repo_root_env: Path) -> None:
        scores_dir = repo_root_env / "nonexistent"
        result = load_reviewer_scores_for_case("case_001", scores_dir)
        assert result == []
