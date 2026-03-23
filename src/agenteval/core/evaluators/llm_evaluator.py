"""LLM-based evaluator for rubric dimensions requiring subjective reasoning."""

from __future__ import annotations

import json
import re
from typing import Any

from agenteval.core.evaluators.llm_provider import LLMProvider, LLMProviderError
from agenteval.core.types import DimensionScoreResult, RubricDimension


def _parse_scale(scale: str) -> tuple[int, int]:
    """Parse '0-2' style scale into (min, max) integers."""
    match = re.match(r"(\d+)\s*-\s*(\d+)", scale)
    if not match:
        return (0, 2)
    return int(match.group(1)), int(match.group(2))


def _build_prompt(trace: dict[str, Any], dim: RubricDimension) -> str:
    """Build the scoring prompt for the LLM."""
    scale_min, scale_max = _parse_scale(dim.scale)
    scoring_guide_text = ""
    if dim.scoring_guide:
        lines = [f"  {k}: {v}" for k, v in dim.scoring_guide.items()]
        scoring_guide_text = "\n".join(lines)

    steps_json = json.dumps(trace.get("steps", []), indent=2, default=str)

    return f"""You are an expert evaluator scoring an AI agent's trace against a rubric dimension.

## Dimension: {dim.title}
**Description**: {dim.description}
**Scale**: {dim.scale} (integer from {scale_min} to {scale_max})

## Scoring Guide
{scoring_guide_text}

## Agent Trace
```json
{steps_json}
```

## Instructions
Analyze the agent trace above and score it on the "{dim.title}" dimension.

You MUST respond with a valid JSON object containing exactly these fields:
- "score": integer from {scale_min} to {scale_max}
- "reasoning": string explaining your score (1-3 sentences)
- "evidence_step_ids": array of step_id strings that support your score
- "confidence": float from 0.0 to 1.0 indicating your confidence

Example response:
{{"score": 1, "reasoning": "The agent ...", "evidence_step_ids": ["s1", "s3"], "confidence": 0.8}}

Respond ONLY with the JSON object, no other text."""


class LLMEvaluator:
    """Score a rubric dimension using an LLM as judge.

    Constructs a prompt from trace + rubric dimension, sends to
    the configured LLM provider, parses the response into a
    DimensionScoreResult with score, reasoning, evidence,
    confidence, and model identifier.
    """

    def __init__(
        self,
        provider: LLMProvider,
        dimension_name: str,
    ) -> None:
        self._provider = provider
        self._dimension_name = dimension_name

    @property
    def dimension_name(self) -> str:
        return self._dimension_name

    def score_dimension(
        self,
        trace: dict[str, Any],
        rubric_dimension: RubricDimension,
    ) -> DimensionScoreResult:
        steps = trace.get("steps", [])
        if not steps:
            return DimensionScoreResult(
                dimension_name=self._dimension_name,
                score=None,
                weight=rubric_dimension.weight,
                scale=rubric_dimension.scale,
                evidence_step_ids=(),
                notes="Empty trace: no steps to analyze.",
                evaluator_type="llm",
                error="empty_trace",
            )

        prompt = _build_prompt(trace, rubric_dimension)

        try:
            response = self._provider.complete(prompt)
        except LLMProviderError as exc:
            return DimensionScoreResult(
                dimension_name=self._dimension_name,
                score=None,
                weight=rubric_dimension.weight,
                scale=rubric_dimension.scale,
                evidence_step_ids=(),
                notes=f"LLM provider error: {exc}",
                evaluator_type="llm",
                error=str(exc),
            )

        return self._parse_llm_response(
            response.text,
            response.model,
            rubric_dimension,
        )

    def _parse_llm_response(
        self,
        text: str,
        model: str,
        rubric_dimension: RubricDimension,
    ) -> DimensionScoreResult:
        """Parse LLM JSON response into DimensionScoreResult."""
        # Try to extract JSON from the response
        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    return self._error_result(
                        rubric_dimension, "invalid_json", "Could not parse LLM response as JSON."
                    )
            else:
                return self._error_result(
                    rubric_dimension, "invalid_json", "Could not parse LLM response as JSON."
                )

        # Extract and validate score
        raw_score = data.get("score")
        if raw_score is None:
            return self._error_result(
                rubric_dimension, "missing_score", "LLM response missing 'score' field."
            )

        try:
            score = int(raw_score)
        except (TypeError, ValueError):
            return self._error_result(
                rubric_dimension,
                "invalid_score_type",
                f"Score is not an integer: {raw_score}",
            )

        # Validate score is within rubric scale range
        scale_min, scale_max = _parse_scale(rubric_dimension.scale)
        if score < scale_min or score > scale_max:
            return self._error_result(
                rubric_dimension,
                "score_out_of_range",
                f"Score {score} outside range {scale_min}-{scale_max}.",
            )

        # Extract optional fields
        reasoning = str(data.get("reasoning", ""))
        evidence = data.get("evidence_step_ids", [])
        if not isinstance(evidence, list):
            evidence = []
        evidence_ids = tuple(str(e) for e in evidence)

        confidence = data.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
                confidence = max(0.0, min(1.0, confidence))
            except (TypeError, ValueError):
                confidence = None

        notes = f"[{model}] {reasoning}" if reasoning else f"[{model}] No reasoning provided."

        return DimensionScoreResult(
            dimension_name=self._dimension_name,
            score=score,
            weight=rubric_dimension.weight,
            scale=rubric_dimension.scale,
            evidence_step_ids=evidence_ids,
            notes=notes,
            evaluator_type="llm",
            confidence=confidence,
        )

    def _error_result(
        self,
        rubric_dimension: RubricDimension,
        error: str,
        notes: str,
    ) -> DimensionScoreResult:
        return DimensionScoreResult(
            dimension_name=self._dimension_name,
            score=None,
            weight=rubric_dimension.weight,
            scale=rubric_dimension.scale,
            evidence_step_ids=(),
            notes=notes,
            evaluator_type="llm",
            error=error,
        )
