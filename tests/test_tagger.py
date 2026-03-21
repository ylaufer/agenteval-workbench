from __future__ import annotations

from typing import Any, Dict

from agenteval.core.tagger import (
    FailureTag,
    _tag_format_violation,
    _tag_hallucination_tool_output,
    _tag_incomplete_execution,
    _tag_ui_mismatch,
    tag_trace,
)


def _step(
    step_id: str = "s1",
    step_type: str = "thought",
    content: str = "",
    **kwargs: Any,
) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "step_id": step_id,
        "type": step_type,
        "actor_id": "agent",
        "content": content,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# _tag_incomplete_execution
# ---------------------------------------------------------------------------


class TestTagIncompleteExecution:
    def test_tool_call_without_observation(self) -> None:
        steps = [
            _step("s1", "tool_call", "call tool", tool_name="search"),
            _step("s2", "final_answer", "done"),
        ]
        assert _tag_incomplete_execution(steps) is True

    def test_tool_call_with_observation(self) -> None:
        steps = [
            _step("s1", "tool_call", "call tool", tool_name="search"),
            _step("s2", "observation", "got result", tool_output="data"),
            _step("s3", "final_answer", "done"),
        ]
        assert _tag_incomplete_execution(steps) is False

    def test_no_tool_calls(self) -> None:
        steps = [
            _step("s1", "thought", "thinking"),
            _step("s2", "final_answer", "answer"),
        ]
        assert _tag_incomplete_execution(steps) is False

    def test_observation_without_tool_output(self) -> None:
        steps = [
            _step("s1", "tool_call", "call tool", tool_name="search"),
            _step("s2", "observation", "empty observation"),
        ]
        assert _tag_incomplete_execution(steps) is True

    def test_multiple_tool_calls_one_incomplete(self) -> None:
        steps = [
            _step("s1", "tool_call", "first call", tool_name="a"),
            _step("s2", "observation", "result", tool_output="data"),
            _step("s3", "tool_call", "second call", tool_name="b"),
            _step("s4", "final_answer", "done"),
        ]
        assert _tag_incomplete_execution(steps) is True


# ---------------------------------------------------------------------------
# _tag_hallucination_tool_output
# ---------------------------------------------------------------------------


class TestTagHallucinationToolOutput:
    def test_contradiction_detected(self) -> None:
        steps = [
            _step("s1", "observation", "", tool_output="the server returned active status data"),
            _step("s2", "final_answer", "The server is not active status data available"),
        ]
        assert _tag_hallucination_tool_output(steps) is True

    def test_no_contradiction(self) -> None:
        steps = [
            _step("s1", "observation", "", tool_output="result is 42"),
            _step("s2", "final_answer", "The result is 42"),
        ]
        assert _tag_hallucination_tool_output(steps) is False

    def test_no_final_answer(self) -> None:
        steps = [
            _step("s1", "observation", "", tool_output="data"),
            _step("s2", "thought", "thinking"),
        ]
        assert _tag_hallucination_tool_output(steps) is False

    def test_no_tool_outputs(self) -> None:
        steps = [
            _step("s1", "thought", "thinking"),
            _step("s2", "final_answer", "answer"),
        ]
        assert _tag_hallucination_tool_output(steps) is False


# ---------------------------------------------------------------------------
# _tag_ui_mismatch
# ---------------------------------------------------------------------------


class TestTagUiMismatch:
    def test_multiple_screenshots_with_state_changes(self) -> None:
        steps = [
            _step("s1", "tool_call", "click button", tool_name="click", screenshot_path="a.png"),
            _step("s2", "observation", "observed", screenshot_path="b.png"),
        ]
        assert _tag_ui_mismatch(steps) is True

    def test_fewer_than_two_screenshots(self) -> None:
        steps = [
            _step("s1", "tool_call", "click", tool_name="click", screenshot_path="a.png"),
            _step("s2", "observation", "ok"),
        ]
        assert _tag_ui_mismatch(steps) is False

    def test_no_screenshots(self) -> None:
        steps = [
            _step("s1", "thought", "thinking"),
            _step("s2", "final_answer", "done"),
        ]
        assert _tag_ui_mismatch(steps) is False


# ---------------------------------------------------------------------------
# _tag_format_violation
# ---------------------------------------------------------------------------


class TestTagFormatViolation:
    def test_json_with_narrative(self) -> None:
        steps = [
            _step("s1", "thought", "Return the answer in JSON format"),
            _step("s2", "final_answer", 'Here is the result: {"key": "value"}'),
        ]
        assert _tag_format_violation(steps) is True

    def test_clean_json(self) -> None:
        steps = [
            _step("s1", "thought", "Return JSON"),
            _step("s2", "final_answer", '{"key": "value"}'),
        ]
        assert _tag_format_violation(steps) is False

    def test_no_format_hints(self) -> None:
        steps = [
            _step("s1", "thought", "Do something"),
            _step("s2", "final_answer", "Here is the answer"),
        ]
        assert _tag_format_violation(steps) is False


# ---------------------------------------------------------------------------
# tag_trace
# ---------------------------------------------------------------------------


class TestTagTrace:
    def test_clean_trace(self) -> None:
        trace: Dict[str, Any] = {
            "steps": [
                _step("s1", "tool_call", "call", tool_name="t"),
                _step("s2", "observation", "result", tool_output="data"),
                _step("s3", "final_answer", "done"),
            ],
        }
        tags = tag_trace(trace)  # type: ignore[arg-type]
        assert isinstance(tags, tuple)

    def test_incomplete_trace(self) -> None:
        trace: Dict[str, Any] = {
            "steps": [
                _step("s1", "tool_call", "call", tool_name="t"),
                _step("s2", "final_answer", "done"),
            ],
        }
        tags = tag_trace(trace)  # type: ignore[arg-type]
        assert FailureTag.INCOMPLETE_EXECUTION in tags

    def test_empty_tuple_for_minimal_clean(self) -> None:
        trace: Dict[str, Any] = {
            "steps": [
                _step("s1", "thought", "thinking"),
                _step("s2", "final_answer", "42"),
            ],
        }
        tags = tag_trace(trace)  # type: ignore[arg-type]
        assert tags == ()
