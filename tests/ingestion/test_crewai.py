"""Tests for CrewAI adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.ingestion.crewai import CrewAIAdapter


@pytest.fixture
def crewai_log_fixture() -> dict:
    """Load CrewAI log fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "crewai_log.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_crewai_adapter_can_handle(crewai_log_fixture: dict) -> None:
    """Test CrewAIAdapter.can_handle() with valid CrewAI log."""
    adapter = CrewAIAdapter()
    assert adapter.can_handle(crewai_log_fixture)


def test_crewai_adapter_can_handle_invalid() -> None:
    """Test CrewAIAdapter.can_handle() rejects invalid format."""
    adapter = CrewAIAdapter()
    assert not adapter.can_handle({"invalid": "data"})


def test_crewai_adapter_convert(crewai_log_fixture: dict) -> None:
    """Test CrewAIAdapter.convert() produces valid trace."""
    adapter = CrewAIAdapter()
    trace = adapter.convert(crewai_log_fixture)

    # Check trace structure
    assert "steps" in trace
    assert len(trace["steps"]) >= 5  # Multiple actions across tasks

    # Check step types
    step_types = {s["type"] for s in trace["steps"]}
    assert "thought" in step_types
    assert "tool_call" in step_types or "observation" in step_types


def test_crewai_agent_to_actor_id(crewai_log_fixture: dict) -> None:
    """Test that agent names are mapped to actor_id."""
    adapter = CrewAIAdapter()
    trace = adapter.convert(crewai_log_fixture)

    # Check that actor_id is populated from agent field
    actors = {s.get("actor_id") for s in trace["steps"] if "actor_id" in s}
    assert "researcher" in actors
    assert "writer" in actors


def test_crewai_task_action_sequence(crewai_log_fixture: dict) -> None:
    """Test that task actions are converted in correct sequence."""
    adapter = CrewAIAdapter()
    trace = adapter.convert(crewai_log_fixture)

    # Steps should be ordered by timestamp
    timestamps = [s["timestamp"] for s in trace["steps"]]
    assert timestamps == sorted(timestamps)

    # First action should be from researcher agent
    first_step = trace["steps"][0]
    assert first_step.get("actor_id") == "researcher"


def test_crewai_malformed_trace() -> None:
    """Test error handling for missing required fields."""
    adapter = CrewAIAdapter()
    malformed = {
        "tasks": [
            {
                "task_id": "t1",
                "actions": [
                    {
                        "type": "thought"
                        # Missing action_id and timestamp (required fields)
                    }
                ]
            }
        ]
    }

    with pytest.raises(ValueError, match="missing required field"):
        adapter.convert(malformed)
