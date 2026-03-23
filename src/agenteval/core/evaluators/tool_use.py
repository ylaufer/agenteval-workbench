"""Rule-based evaluator for the tool_use rubric dimension."""

from __future__ import annotations

from typing import Any, Sequence

from agenteval.core.types import DimensionScoreResult, RubricDimension


class ToolUseEvaluator:
    """Score tool_use dimension using trace analysis.

    Scoring logic (0-2 scale):
    - 0: Tool call without observation, hallucinated tool output, or schema misuse
    - 1: Tools used correctly but with unnecessary calls or minor inefficiency
    - 2: All tools used correctly and efficiently
    """

    @property
    def dimension_name(self) -> str:
        return "tool_use"

    def score_dimension(
        self,
        trace: dict[str, Any],
        rubric_dimension: RubricDimension,
    ) -> DimensionScoreResult:
        steps: Sequence[dict[str, Any]] = trace.get("steps", [])

        if not steps:
            return DimensionScoreResult(
                dimension_name=self.dimension_name,
                score=None,
                weight=rubric_dimension.weight,
                scale=rubric_dimension.scale,
                evidence_step_ids=(),
                notes="Empty trace: no steps to analyze.",
                evaluator_type="rule",
                error="empty_trace",
            )

        tool_calls = [s for s in steps if s.get("type") == "tool_call"]
        if not tool_calls:
            # No tool calls — tool_use is not applicable, score max
            return DimensionScoreResult(
                dimension_name=self.dimension_name,
                score=2,
                weight=rubric_dimension.weight,
                scale=rubric_dimension.scale,
                evidence_step_ids=(),
                notes="No tool calls in trace; tool_use dimension not applicable.",
                evaluator_type="rule",
            )

        evidence: list[str] = []
        issues: list[str] = []
        has_incomplete = False
        has_hallucination = False
        unnecessary_count = 0

        for i, step in enumerate(steps):
            if step.get("type") != "tool_call":
                continue

            step_id = step.get("step_id", f"step_{i}")

            # Check: tool call followed by observation with output?
            has_observation = False
            for j in range(i + 1, len(steps)):
                next_step = steps[j]
                if next_step.get("type") == "observation":
                    if next_step.get("tool_output") is not None:
                        has_observation = True
                    break

            if not has_observation:
                has_incomplete = True
                evidence.append(step_id)
                issues.append(f"{step_id}: tool call without observation/output")

            # Check: duplicate tool calls (same tool_name + tool_input in sequence)
            tool_name = step.get("tool_name", "")
            tool_input = step.get("tool_input")
            for k in range(i + 1, len(steps)):
                later = steps[k]
                if later.get("type") != "tool_call":
                    continue
                if later.get("tool_name") == tool_name and later.get("tool_input") == tool_input:
                    unnecessary_count += 1
                    evidence.append(later.get("step_id", f"step_{k}"))
                    issues.append(
                        f"{later.get('step_id', f'step_{k}')}: duplicate call to {tool_name}"
                    )
                break  # only check next tool call

        # Check hallucination: final answer contradicts tool output
        final_answers = [s for s in steps if s.get("type") == "final_answer"]
        tool_outputs = [
            s.get("tool_output", "")
            for s in steps
            if s.get("type") == "observation" and s.get("tool_output")
        ]
        if final_answers and tool_outputs:
            fa_content = str(final_answers[-1].get("content", "")).lower()
            for to in tool_outputs:
                to_str = str(to).lower()
                if to_str and len(to_str) > 10:
                    key_terms = to_str.split()[:5]
                    if any(term in fa_content for term in key_terms):
                        if "not " in fa_content or " no " in fa_content:
                            has_hallucination = True
                            fa_id = final_answers[-1].get("step_id", "final")
                            evidence.append(fa_id)
                            issues.append(f"{fa_id}: final answer may contradict tool output")

        # Determine score
        if has_incomplete or has_hallucination:
            score = 0
        elif unnecessary_count > 0:
            score = 1
        else:
            score = 2

        notes = "; ".join(issues) if issues else "All tools used correctly and efficiently."

        return DimensionScoreResult(
            dimension_name=self.dimension_name,
            score=score,
            weight=rubric_dimension.weight,
            scale=rubric_dimension.scale,
            evidence_step_ids=tuple(evidence),
            notes=notes,
            evaluator_type="rule",
        )
