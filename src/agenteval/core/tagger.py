from __future__ import annotations

from typing import Sequence

from agenteval.schemas.trace import Step, Trace


class FailureTag:
    """Canonical failure tags based on observation patterns."""

    INCOMPLETE_EXECUTION = "incomplete_execution"
    HALLUCINATION_TOOL_OUTPUT = "hallucination_tool_output"
    UI_MISMATCH = "ui_mismatch"
    FORMAT_VIOLATION = "format_violation"

    # Helper for iteration
    ALL = [
        INCOMPLETE_EXECUTION,
        HALLUCINATION_TOOL_OUTPUT,
        UI_MISMATCH,
        FORMAT_VIOLATION,
    ]


def _tag_incomplete_execution(steps: Sequence[Step]) -> bool:
    """
    Detect: Tool call without output (observable via missing tool_output or no observation step).
    Pattern: tool_call step not followed by observation with tool_output.
    """
    for i, step in enumerate(steps):
        if step["type"] == "tool_call":
            # Check if there's a following observation step with output
            has_observation_with_output = False
            for j in range(i + 1, len(steps)):
                next_step = steps[j]
                if next_step["type"] == "observation":
                    if next_step.get("tool_output") is not None:
                        has_observation_with_output = True
                    break
            if not has_observation_with_output:
                return True
    return False


def _tag_hallucination_tool_output(steps: Sequence[Step]) -> bool:
    """
    Detect: Final answer contradicts tool output.
    Pattern: final_answer content directly contradicts or ignores documented tool_output.
    """
    final_answer_content: str | None = None
    tool_outputs: list[str] = []

    for step in steps:
        if step["type"] == "final_answer":
            final_answer_content = step.get("content", "")
        if step["type"] == "observation" and step.get("tool_output"):
            output = step["tool_output"]
            if isinstance(output, str):
                tool_outputs.append(output.lower())
            elif isinstance(output, dict):
                tool_outputs.append(str(output).lower())

    if final_answer_content and tool_outputs:
        final_lower = final_answer_content.lower()
        # Simple heuristic: if final answer contains explicit negation or contradiction
        # of tool output content, flag it
        for tool_output in tool_outputs:
            if tool_output and ("no" in final_lower or "not" in final_lower):
                if len(tool_output) > 10:  # Only for meaningful outputs
                    # Check for explicit contradiction
                    key_terms = tool_output.split()[:5]  # First few terms
                    if any(term in final_lower for term in key_terms):
                        if "not " in final_lower or " no " in final_lower:
                            return True
    return False


def _tag_ui_mismatch(steps: Sequence[Step]) -> bool:
    """
    Detect: Screenshot mismatch or UI state discrepancy.
    Pattern: Multiple screenshot_path references that contradict step descriptions.
    """
    screenshots = [s for s in steps if s.get("screenshot_path")]
    if len(screenshots) < 2:
        return False

    # Simple heuristic: if there are screenshots but tool outputs suggest state changes
    # that contradict expected UI states, flag it
    has_state_change = any(step.get("type") in ["tool_call", "observation"] for step in steps)
    return len(screenshots) >= 2 and has_state_change


def _tag_format_violation(steps: Sequence[Step]) -> bool:
    """
    Detect: Extra commentary in JSON-only or format-constrained tasks.
    Pattern: final_answer contains narrative text in a task marked as JSON-only.
    """
    final_answer_content: str | None = None
    task_hints: set[str] = set()

    for step in steps:
        if step["type"] == "final_answer":
            final_answer_content = step.get("content", "")
        # Check for format-related hints in step content
        content_lower = step.get("content", "").lower()
        if "json" in content_lower:
            task_hints.add("json_only")
        if "format" in content_lower:
            task_hints.add("format_constrained")

    if final_answer_content and "json_only" in task_hints:
        # If the final answer has narrative text alongside JSON, it's a violation
        content_lower = final_answer_content.lower()
        has_narrative = any(
            word in content_lower for word in ["the ", "this ", "here ", "note:", "comment:"]
        )
        has_json = "{" in final_answer_content or "[" in final_answer_content
        if has_narrative and has_json:
            return True

    return False


def tag_trace(trace: Trace) -> tuple[str, ...]:
    """
    Analyze a trace and return applicable failure and structural tags.

    Args:
        trace: The evaluation trace to analyze.

    Returns:
        Tuple of applicable tag strings: failure-pattern tags from FailureTag
        followed by structural tags (has_tool_calls, multi_step, has_final_answer).
    """
    steps = trace["steps"]
    tags: list[str] = []

    if _tag_incomplete_execution(steps):
        tags.append(FailureTag.INCOMPLETE_EXECUTION)

    if _tag_hallucination_tool_output(steps):
        tags.append(FailureTag.HALLUCINATION_TOOL_OUTPUT)

    if _tag_ui_mismatch(steps):
        tags.append(FailureTag.UI_MISMATCH)

    if _tag_format_violation(steps):
        tags.append(FailureTag.FORMAT_VIOLATION)

    # Structural tags — derived from step composition, not failure patterns
    if any(s["type"] == "tool_call" for s in steps):
        tags.append("has_tool_calls")
    if len(steps) > 3:
        tags.append("multi_step")
    if any(s["type"] == "final_answer" for s in steps):
        tags.append("has_final_answer")

    return tuple(tags)
