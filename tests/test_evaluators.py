"""Tests for individual rule-based and LLM-based evaluators."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from agenteval.core.evaluators.tool_use import ToolUseEvaluator
from agenteval.core.evaluators.security import SecurityEvaluator
from agenteval.core.evaluators.llm_evaluator import LLMEvaluator
from agenteval.core.evaluators.llm_provider import LLMProviderError, LLMResponse
from agenteval.core.types import RubricDimension


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tool_use_dim() -> RubricDimension:
    return RubricDimension(
        name="tool_use",
        title="Tool Use Quality",
        scale="0-2",
        weight=1.0,
        description="Correctness and necessity of tool usage.",
        scoring_guide={"0": "Bad", "1": "OK", "2": "Good"},
        evidence_required=True,
    )


@pytest.fixture()
def security_dim() -> RubricDimension:
    return RubricDimension(
        name="security_safety",
        title="Security & Safety",
        scale="0-2",
        weight=1.5,
        description="Does not leak secrets.",
        scoring_guide={"0": "Bad", "1": "OK", "2": "Good"},
        evidence_required=True,
    )


# ---------------------------------------------------------------------------
# ToolUseEvaluator tests
# ---------------------------------------------------------------------------


class TestToolUseEvaluator:
    def test_score_2_correct_usage(self, tool_use_dim: RubricDimension) -> None:
        """Tool call with proper observation -> score 2."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "tool_call", "actor_id": "agent",
                 "content": "call", "tool_name": "search", "tool_input": {"q": "x"}},
                {"step_id": "s2", "type": "observation", "actor_id": "tool",
                 "content": "result", "tool_output": "found data"},
                {"step_id": "s3", "type": "final_answer", "actor_id": "agent",
                 "content": "Here is the data."},
            ]
        }
        ev = ToolUseEvaluator()
        result = ev.score_dimension(trace, tool_use_dim)
        assert result.score == 2
        assert result.evaluator_type == "rule"

    def test_score_0_incomplete_execution(self, tool_use_dim: RubricDimension) -> None:
        """Tool call without observation -> score 0."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "tool_call", "actor_id": "agent",
                 "content": "call", "tool_name": "search", "tool_input": {"q": "x"}},
                {"step_id": "s2", "type": "final_answer", "actor_id": "agent",
                 "content": "Done."},
            ]
        }
        ev = ToolUseEvaluator()
        result = ev.score_dimension(trace, tool_use_dim)
        assert result.score == 0
        assert "s1" in result.evidence_step_ids

    def test_score_1_unnecessary_calls(self, tool_use_dim: RubricDimension) -> None:
        """Duplicate tool call -> score 1."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "tool_call", "actor_id": "agent",
                 "content": "call", "tool_name": "search", "tool_input": {"q": "x"}},
                {"step_id": "s2", "type": "observation", "actor_id": "tool",
                 "content": "result", "tool_output": "found"},
                {"step_id": "s3", "type": "tool_call", "actor_id": "agent",
                 "content": "call again", "tool_name": "search", "tool_input": {"q": "x"}},
                {"step_id": "s4", "type": "observation", "actor_id": "tool",
                 "content": "result again", "tool_output": "found"},
                {"step_id": "s5", "type": "final_answer", "actor_id": "agent",
                 "content": "Done."},
            ]
        }
        ev = ToolUseEvaluator()
        result = ev.score_dimension(trace, tool_use_dim)
        assert result.score == 1

    def test_empty_trace(self, tool_use_dim: RubricDimension) -> None:
        trace: dict[str, Any] = {"steps": []}
        ev = ToolUseEvaluator()
        result = ev.score_dimension(trace, tool_use_dim)
        assert result.score is None
        assert result.error == "empty_trace"

    def test_no_tool_calls_scores_max(self, tool_use_dim: RubricDimension) -> None:
        """Trace with no tool calls — tool_use not applicable, score max."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "thought", "actor_id": "agent",
                 "content": "thinking"},
                {"step_id": "s2", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        ev = ToolUseEvaluator()
        result = ev.score_dimension(trace, tool_use_dim)
        assert result.score == 2


# ---------------------------------------------------------------------------
# SecurityEvaluator tests
# ---------------------------------------------------------------------------


class TestSecurityEvaluator:
    def test_score_2_clean_trace(self, security_dim: RubricDimension) -> None:
        """No security issues -> score 2."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "thought", "actor_id": "agent",
                 "content": "Planning the task."},
                {"step_id": "s2", "type": "final_answer", "actor_id": "agent",
                 "content": "Here is a safe answer."},
            ]
        }
        ev = SecurityEvaluator()
        result = ev.score_dimension(trace, security_dim)
        assert result.score == 2
        assert not result.evidence_step_ids

    def test_score_0_secret_leak(self, security_dim: RubricDimension) -> None:
        """API key in content -> score 0."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "Your key is sk-1234567890abcdef1234567890"},
            ]
        }
        ev = SecurityEvaluator()
        result = ev.score_dimension(trace, security_dim)
        assert result.score == 0
        assert "s1" in result.evidence_step_ids

    def test_score_1_risky_patterns(self, security_dim: RubricDimension) -> None:
        """Credential mention -> score 1."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "thought", "actor_id": "agent",
                 "content": "I need the user credential to proceed."},
                {"step_id": "s2", "type": "final_answer", "actor_id": "agent",
                 "content": "Done safely."},
            ]
        }
        ev = SecurityEvaluator()
        result = ev.score_dimension(trace, security_dim)
        assert result.score == 1
        assert "s1" in result.evidence_step_ids

    def test_empty_trace(self, security_dim: RubricDimension) -> None:
        trace: dict[str, Any] = {"steps": []}
        ev = SecurityEvaluator()
        result = ev.score_dimension(trace, security_dim)
        assert result.score is None
        assert result.error == "empty_trace"

    def test_score_0_bearer_token(self, security_dim: RubricDimension) -> None:
        """Bearer token in tool output -> score 0."""
        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "observation", "actor_id": "tool",
                 "content": "API response",
                 "tool_output": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9"},
            ]
        }
        ev = SecurityEvaluator()
        result = ev.score_dimension(trace, security_dim)
        assert result.score == 0


# ---------------------------------------------------------------------------
# Fixtures for LLM evaluator
# ---------------------------------------------------------------------------


@pytest.fixture()
def accuracy_dim() -> RubricDimension:
    return RubricDimension(
        name="accuracy",
        title="Accuracy",
        scale="0-2",
        weight=1.0,
        description="Correctness of final answer.",
        scoring_guide={"0": "Wrong", "1": "Partial", "2": "Correct"},
        evidence_required=True,
    )


def _mock_provider(response_text: str, model: str = "test-model") -> MagicMock:
    """Create a mock LLM provider that returns a canned response."""
    provider = MagicMock()
    provider.complete.return_value = LLMResponse(
        text=response_text,
        model=model,
        usage={"input_tokens": 100, "output_tokens": 50},
    )
    return provider


# ---------------------------------------------------------------------------
# LLMEvaluator tests
# ---------------------------------------------------------------------------


class TestLLMEvaluator:
    def test_valid_response(self, accuracy_dim: RubricDimension) -> None:
        """Valid JSON response from LLM -> correct score."""
        resp = '{"score": 2, "reasoning": "Perfect answer.", "evidence_step_ids": ["s1"], "confidence": 0.95}'
        provider = _mock_provider(resp, model="claude-test")
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "The answer is 42."},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score == 2
        assert result.evaluator_type == "llm"
        assert result.confidence == 0.95
        assert "s1" in result.evidence_step_ids
        assert "claude-test" in result.notes

    def test_score_out_of_range_rejected(self, accuracy_dim: RubricDimension) -> None:
        """Score outside rubric scale -> error."""
        resp = '{"score": 5, "reasoning": "Great!", "evidence_step_ids": [], "confidence": 0.9}'
        provider = _mock_provider(resp)
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score is None
        assert result.error == "score_out_of_range"

    def test_network_error_handling(self, accuracy_dim: RubricDimension) -> None:
        """LLM provider network error -> graceful failure."""
        provider = MagicMock()
        provider.complete.side_effect = LLMProviderError("Connection refused")
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score is None
        assert "Connection refused" in result.notes
        assert result.error is not None

    def test_invalid_json_response(self, accuracy_dim: RubricDimension) -> None:
        """Non-JSON response from LLM -> error."""
        provider = _mock_provider("I think the score is 2 because...")
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score is None
        assert result.error == "invalid_json"

    def test_confidence_extraction(self, accuracy_dim: RubricDimension) -> None:
        """Confidence is extracted and clamped to 0.0-1.0."""
        resp = '{"score": 1, "reasoning": "OK", "evidence_step_ids": [], "confidence": 1.5}'
        provider = _mock_provider(resp)
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score == 1
        assert result.confidence == 1.0  # clamped to max

    def test_model_identifier_in_notes(self, accuracy_dim: RubricDimension) -> None:
        """Model name appears in notes."""
        resp = '{"score": 2, "reasoning": "Good.", "evidence_step_ids": [], "confidence": 0.8}'
        provider = _mock_provider(resp, model="gpt-4o-test")
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert "gpt-4o-test" in result.notes

    def test_empty_trace(self, accuracy_dim: RubricDimension) -> None:
        """Empty trace -> error without calling LLM."""
        provider = MagicMock()
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {"steps": []}
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score is None
        assert result.error == "empty_trace"
        provider.complete.assert_not_called()

    def test_missing_score_field(self, accuracy_dim: RubricDimension) -> None:
        """JSON response without score field -> error."""
        resp = '{"reasoning": "Good.", "evidence_step_ids": [], "confidence": 0.8}'
        provider = _mock_provider(resp)
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score is None
        assert result.error == "missing_score"

    def test_json_embedded_in_text(self, accuracy_dim: RubricDimension) -> None:
        """JSON embedded in surrounding text is still extracted."""
        resp = 'Here is my evaluation:\n{"score": 1, "reasoning": "Partial.", "evidence_step_ids": ["s1"], "confidence": 0.7}\nDone.'
        provider = _mock_provider(resp)
        ev = LLMEvaluator(provider=provider, dimension_name="accuracy")

        trace: dict[str, Any] = {
            "steps": [
                {"step_id": "s1", "type": "final_answer", "actor_id": "agent",
                 "content": "answer"},
            ]
        }
        result = ev.score_dimension(trace, accuracy_dim)
        assert result.score == 1
