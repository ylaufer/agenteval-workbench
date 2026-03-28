from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class RunStatus(str, Enum):
    """Lifecycle state of an evaluation run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RunRecord:
    """Metadata for a single evaluation run. Persisted as runs/<run_id>/run.json."""

    run_id: str
    status: str
    started_at: str
    dataset_dir: str
    rubric_path: str
    num_cases: int = 0
    completed_at: str | None = None
    error: str | None = None
    filter_criteria: dict[str, Any] | None = field(default=None)


@dataclass(frozen=True)
class RubricDimension:
    name: str
    title: str | None
    scale: str
    weight: float
    description: str
    scoring_guide: Mapping[str, str]
    evidence_required: bool


@dataclass(frozen=True)
class Rubric:
    version: str
    name: str | None
    security_redact_patterns: tuple[str, ...]
    dimensions: tuple[RubricDimension, ...]


@dataclass(frozen=True)
class DimensionScore:
    """A single reviewer's score for one rubric dimension."""

    score: int
    evidence_step_ids: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class ReviewerScore:
    """Complete scoring by one reviewer for one benchmark case."""

    case_id: str
    reviewer_id: str
    rubric_version: str
    timestamp: str
    dimensions: Mapping[str, DimensionScore] = field(default_factory=dict)
    overall_notes: str = ""


@dataclass(frozen=True)
class DimensionEvaluationTemplate:
    """Template for a single rubric dimension evaluation."""

    dimension_name: str
    score: int | None
    weight: float
    scale: str
    evidence_step_ids: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class CaseEvaluationTemplate:
    """Structured evaluation template for a single benchmark case."""

    case_id: str
    task_id: str
    rubric_version: str
    rubric_name: str | None
    primary_failure: str | None
    secondary_failures: tuple[str, ...]
    severity: str | None
    auto_tags: tuple[str, ...]
    trace_summary: Mapping[str, object]
    dimensions: Mapping[str, DimensionEvaluationTemplate]
    labels: Sequence[str]
    case_version: str | None = None


@dataclass(frozen=True)
class DimensionScoreResult:
    """Output of a single evaluator for one rubric dimension."""

    dimension_name: str
    score: int | None
    weight: float
    scale: str
    evidence_step_ids: tuple[str, ...]
    notes: str
    evaluator_type: str  # "rule" or "llm"
    confidence: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class AutoEvaluation:
    """Complete auto-scoring result for a single benchmark case."""

    case_id: str
    scoring_type: str  # always "auto"
    rubric_version: str
    dimensions: Mapping[str, DimensionScoreResult]
    auto_tags: tuple[str, ...]
    metadata: Mapping[str, Any]
