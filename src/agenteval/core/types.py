from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


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
    trace_summary: Mapping[str, object]
    dimensions: Mapping[str, DimensionEvaluationTemplate]
    labels: Sequence[str]

