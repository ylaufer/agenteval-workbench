"""Tests for OpenAI Raw API adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.ingestion.openai_raw import OpenAIRawAdapter


@pytest.fixture
def openai_response_fixture() -> dict:
    """Load OpenAI response fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "openai_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_openai_raw_adapter_can_handle(openai_response_fixture: dict) -> None:
    """Test OpenAIRawAdapter.can_handle() with valid OpenAI response."""
    adapter = OpenAIRawAdapter()
    assert adapter.can_handle(openai_response_fixture)


def test_openai_raw_adapter_can_handle_invalid() -> None:
    """Test OpenAIRawAdapter.can_handle() rejects invalid format."""
    adapter = OpenAIRawAdapter()
    assert not adapter.can_handle({"invalid": "data"})


def test_openai_raw_adapter_convert(openai_response_fixture: dict) -> None:
    """Test OpenAIRawAdapter.convert() produces valid trace."""
    adapter = OpenAIRawAdapter()
    trace = adapter.convert(openai_response_fixture)

    # Check trace structure
    assert "steps" in trace
    assert len(trace["steps"]) >= 3  # tool_calls + observations + final answer

    # Check step types
    step_types = {s["type"] for s in trace["steps"]}
    assert "tool_call" in step_types
    assert "observation" in step_types
    assert "final_answer" in step_types


def test_openai_message_to_step_conversion(openai_response_fixture: dict) -> None:
    """Test that messages are converted to steps correctly."""
    adapter = OpenAIRawAdapter()
    trace = adapter.convert(openai_response_fixture)

    # User messages should be skipped (not converted to steps)
    # Only assistant and tool messages should create steps
    assert all(s["type"] != "user" for s in trace["steps"])


def test_openai_parallel_tool_calls(openai_response_fixture: dict) -> None:
    """Test handling of parallel tool calls."""
    adapter = OpenAIRawAdapter()
    trace = adapter.convert(openai_response_fixture)

    # Should have tool_call steps for both get_weather and get_time
    tool_calls = [s for s in trace["steps"] if s["type"] == "tool_call"]
    tool_names = {s.get("tool_name") for s in tool_calls}

    assert "get_weather" in tool_names
    assert "get_time" in tool_names
    assert len(tool_calls) == 2  # Parallel tool calls


def test_openai_final_answer_heuristic(openai_response_fixture: dict) -> None:
    """Test that final assistant message is marked as final_answer."""
    adapter = OpenAIRawAdapter()
    trace = adapter.convert(openai_response_fixture)

    # Last step should be final_answer
    final_answers = [s for s in trace["steps"] if s["type"] == "final_answer"]
    assert len(final_answers) == 1

    # Final answer should contain the summary
    assert "Boston" in final_answers[0]["content"]
    assert "15°C" in final_answers[0]["content"]


def test_openai_malformed_trace() -> None:
    """Test error handling for malformed OpenAI response."""
    adapter = OpenAIRawAdapter()
    # This will pass can_handle() but fail on conversion (empty messages)
    malformed = {"messages": [{"role": "user", "content": "test"}]}  # Only user message, no assistant responses

    # Should still work but create minimal trace
    trace = adapter.convert(malformed)
    assert len(trace["steps"]) == 0  # User messages are skipped
