"""Pluggable evaluator framework for auto-scoring."""

from __future__ import annotations

from typing import Any

from agenteval.core.evaluators.base import Evaluator
from agenteval.core.types import DimensionScoreResult, Rubric


class EvaluatorRegistry:
    """Maps rubric dimension names to evaluator instances."""

    def __init__(self) -> None:
        self._evaluators: dict[str, Evaluator] = {}

    def register(self, evaluator: Evaluator) -> None:
        """Register an evaluator for its dimension. Overwrites any existing."""
        self._evaluators[evaluator.dimension_name] = evaluator

    def get(self, dimension_name: str) -> Evaluator | None:
        """Return the evaluator for a dimension, or None."""
        return self._evaluators.get(dimension_name)

    def registered_dimensions(self) -> list[str]:
        """Return list of dimension names with registered evaluators."""
        return list(self._evaluators.keys())

    def score_all(
        self,
        trace: dict[str, Any],
        rubric: Rubric,
    ) -> dict[str, DimensionScoreResult]:
        """Score all registered dimensions.

        Non-registered dimensions are skipped.
        Errors in individual evaluators are captured, not raised.
        """
        results: dict[str, DimensionScoreResult] = {}
        for dim in rubric.dimensions:
            evaluator = self._evaluators.get(dim.name)
            if evaluator is None:
                continue
            try:
                result = evaluator.score_dimension(trace, dim)
                results[dim.name] = result
            except Exception as exc:
                results[dim.name] = DimensionScoreResult(
                    dimension_name=dim.name,
                    score=None,
                    weight=dim.weight,
                    scale=dim.scale,
                    evidence_step_ids=(),
                    notes="",
                    evaluator_type="rule",
                    error=str(exc),
                )
        return results
