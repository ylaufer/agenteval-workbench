"""Tests for LangChain adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.ingestion.langchain import LangChainAdapter


@pytest.fixture
def langchain_run_fixture() -> dict:
    """Load LangChain run fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "langchain_run.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_langchain_adapter_can_handle(langchain_run_fixture: dict) -> None:
    """Test LangChainAdapter.can_handle() with valid LangChain run."""
    adapter = LangChainAdapter()
    assert adapter.can_handle(langchain_run_fixture)


def test_langchain_adapter_can_handle_invalid() -> None:
    """Test LangChainAdapter.can_handle() rejects invalid format."""
    adapter = LangChainAdapter()
    assert not adapter.can_handle({"invalid": "data"})


def test_langchain_adapter_convert(langchain_run_fixture: dict) -> None:
    """Test LangChainAdapter.convert() produces valid trace."""
    adapter = LangChainAdapter()
    trace = adapter.convert(langchain_run_fixture)

    # Check trace structure
    assert "steps" in trace
    assert len(trace["steps"]) >= 3  # At least llm, tool, llm steps

    # Check for tool expansion (tool_call + observation)
    tool_related_steps = [s for s in trace["steps"] if s.get("tool_name") == "weather_api" or "weather_api" in s.get("content", "")]
    assert len(tool_related_steps) >= 1  # Tool run should create at least one step


def test_langchain_run_tree_flattening(langchain_run_fixture: dict) -> None:
    """Test that nested run tree is flattened correctly."""
    adapter = LangChainAdapter()
    trace = adapter.convert(langchain_run_fixture)

    # All child runs should be flattened into steps
    assert len(trace["steps"]) >= len(langchain_run_fixture["child_runs"])

    # Steps should be ordered by timestamp
    timestamps = [s["timestamp"] for s in trace["steps"]]
    assert timestamps == sorted(timestamps)


def test_langchain_tool_run_expansion(langchain_run_fixture: dict) -> None:
    """Test that tool runs expand to tool_call + observation steps."""
    adapter = LangChainAdapter()
    trace = adapter.convert(langchain_run_fixture)

    # Find tool-related steps
    tool_steps = [s for s in trace["steps"] if s.get("type") in ["tool_call", "observation"]]

    # Should have at least tool_call and observation for the weather_api tool
    assert len(tool_steps) >= 2


def test_langchain_malformed_trace() -> None:
    """Test error handling for malformed LangChain run."""
    adapter = LangChainAdapter()
    malformed = {"run_type": "chain", "id": "test"}  # Missing start_time

    with pytest.raises(ValueError, match="missing required field"):
        adapter.convert(malformed)
