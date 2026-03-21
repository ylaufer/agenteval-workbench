from __future__ import annotations

import dataclasses

import pytest

from agenteval.core.types import (
    CaseEvaluationTemplate,
    DimensionEvaluationTemplate,
    DimensionScore,
    ReviewerScore,
    Rubric,
    RubricDimension,
)


class TestRubricDimension:
    def test_construct(self) -> None:
        dim = RubricDimension(
            name="accuracy",
            title="Accuracy",
            scale="0-2",
            weight=1.0,
            description="desc",
            scoring_guide={"0": "bad", "2": "good"},
            evidence_required=True,
        )
        assert dim.name == "accuracy"
        assert dim.weight == 1.0

    def test_frozen(self) -> None:
        dim = RubricDimension(
            name="x",
            title=None,
            scale="0-2",
            weight=1.0,
            description="d",
            scoring_guide={},
            evidence_required=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            dim.name = "y"  # type: ignore[misc]


class TestRubric:
    def test_construct(self) -> None:
        rubric = Rubric(
            version="v1",
            name="Test",
            security_redact_patterns=("sk-.*",),
            dimensions=(),
        )
        assert rubric.version == "v1"
        assert rubric.security_redact_patterns == ("sk-.*",)

    def test_frozen(self) -> None:
        rubric = Rubric(version="v1", name=None, security_redact_patterns=(), dimensions=())
        with pytest.raises(dataclasses.FrozenInstanceError):
            rubric.version = "v2"  # type: ignore[misc]


class TestDimensionScore:
    def test_defaults(self) -> None:
        ds = DimensionScore(score=2)
        assert ds.evidence_step_ids == ()
        assert ds.notes == ""

    def test_full(self) -> None:
        ds = DimensionScore(score=1, evidence_step_ids=("s1", "s2"), notes="ok")
        assert ds.score == 1
        assert ds.evidence_step_ids == ("s1", "s2")

    def test_frozen(self) -> None:
        ds = DimensionScore(score=0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            ds.score = 1  # type: ignore[misc]


class TestReviewerScore:
    def test_defaults(self) -> None:
        rs = ReviewerScore(
            case_id="c1",
            reviewer_id="alice",
            rubric_version="v1",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert rs.dimensions == {}
        assert rs.overall_notes == ""

    def test_full(self) -> None:
        rs = ReviewerScore(
            case_id="c1",
            reviewer_id="bob",
            rubric_version="v1",
            timestamp="t",
            dimensions={"accuracy": DimensionScore(score=2)},
            overall_notes="Great",
        )
        assert rs.dimensions["accuracy"].score == 2

    def test_frozen(self) -> None:
        rs = ReviewerScore(
            case_id="c1",
            reviewer_id="r",
            rubric_version="v1",
            timestamp="t",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            rs.case_id = "c2"  # type: ignore[misc]


class TestDimensionEvaluationTemplate:
    def test_construct(self) -> None:
        det = DimensionEvaluationTemplate(
            dimension_name="accuracy",
            score=None,
            weight=1.0,
            scale="0-2",
            evidence_step_ids=(),
            notes="",
        )
        assert det.score is None
        assert det.weight == 1.0


class TestCaseEvaluationTemplate:
    def test_construct(self) -> None:
        cet = CaseEvaluationTemplate(
            case_id="case_001",
            task_id="task_001",
            rubric_version="v1",
            rubric_name="Test",
            primary_failure=None,
            secondary_failures=(),
            severity=None,
            auto_tags=(),
            trace_summary={},
            dimensions={},
            labels=[],
        )
        assert cet.case_id == "case_001"

    def test_frozen(self) -> None:
        cet = CaseEvaluationTemplate(
            case_id="c",
            task_id="t",
            rubric_version="v",
            rubric_name=None,
            primary_failure=None,
            secondary_failures=(),
            severity=None,
            auto_tags=(),
            trace_summary={},
            dimensions={},
            labels=[],
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            cet.case_id = "x"  # type: ignore[misc]
