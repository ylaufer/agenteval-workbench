"""Abstract evaluator protocol for auto-scoring."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agenteval.core.types import DimensionScoreResult, RubricDimension


@runtime_checkable
class Evaluator(Protocol):
    """Protocol that all evaluators must implement."""

    @property
    def dimension_name(self) -> str:
        """The rubric dimension this evaluator scores."""
        ...

    def score_dimension(
        self,
        trace: dict[str, Any],
        rubric_dimension: RubricDimension,
    ) -> DimensionScoreResult:
        """Score a single rubric dimension given trace data.

        Must not raise exceptions — returns DimensionScoreResult with
        error field populated on failure.
        """
        ...
