"""Tests for Generic JSON adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.ingestion.generic import GenericAdapter


@pytest.fixture
def custom_mapping_fixture() -> dict:
    """Load custom mapping config."""
    mapping_path = Path(__file__).parent / "fixtures" / "custom_mapping.yaml"

    # Try to load YAML, fall back to manual dict if pyyaml not available
    try:
        import yaml

        with open(mapping_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        # YAML not available - use hardcoded mapping for tests
        return {
            "task_id": "execution.run_id",
            "user_prompt": "execution.input_query",
            "model_version": "execution.model_name",
            "steps_path": "execution.events",
            "step_mappings": {
                "step_id": "event_id",
                "type": {
                    "path": "event_type",
                    "transform": "map",
                    "mapping": {
                        "think": "thought",
                        "call_tool": "tool_call",
                        "tool_result": "observation",
                        "answer": "final_answer",
                    },
                },
                "content": "event_data.text",
                "timestamp": {"path": "created_at", "transform": "iso8601"},
                "tool_name": "event_data.tool_id",
                "actor_id": "event_data.agent_name",
            },
            "metadata_timestamp": "execution.started_at",
            "metadata_source": "custom",
        }


@pytest.fixture
def custom_trace_fixture() -> dict:
    """Load custom trace fixture."""
    trace_path = Path(__file__).parent / "fixtures" / "custom_trace.json"
    with open(trace_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_generic_adapter_can_handle(custom_trace_fixture: dict, custom_mapping_fixture: dict) -> None:
    """Test GenericAdapter.can_handle() with mapping."""
    adapter = GenericAdapter(custom_mapping_fixture)
    # Generic adapter always returns True (it's a fallback)
    assert adapter.can_handle(custom_trace_fixture)


def test_generic_adapter_convert(custom_trace_fixture: dict, custom_mapping_fixture: dict) -> None:
    """Test GenericAdapter.convert() produces valid trace."""
    adapter = GenericAdapter(custom_mapping_fixture)
    trace = adapter.convert(custom_trace_fixture)

    # Check trace structure
    assert trace["task_id"] == "custom-run-001"
    assert trace["user_prompt"] == "Analyze the sales data"
    assert trace["model_version"] == "custom-agent-v1"
    assert len(trace["steps"]) == 5


def test_generic_path_extraction(custom_trace_fixture: dict, custom_mapping_fixture: dict) -> None:
    """Test JSONPath-like field extraction."""
    adapter = GenericAdapter(custom_mapping_fixture)
    trace = adapter.convert(custom_trace_fixture)

    # Check extracted fields
    first_step = trace["steps"][0]
    assert first_step["step_id"] == "evt-001"
    assert first_step["type"] == "thought"  # Mapped from "think"
    assert first_step["content"] == "I need to load the sales data file first."
    assert first_step["actor_id"] == "analyst"


def test_generic_transform_functions(custom_trace_fixture: dict, custom_mapping_fixture: dict) -> None:
    """Test transform functions (map, iso8601, concat)."""
    adapter = GenericAdapter(custom_mapping_fixture)
    trace = adapter.convert(custom_trace_fixture)

    # Test 'map' transform (event_type → type)
    step_types = [s["type"] for s in trace["steps"]]
    assert "thought" in step_types
    assert "tool_call" in step_types
    assert "observation" in step_types
    assert "final_answer" in step_types

    # Test 'iso8601' transform (timestamps should be preserved)
    assert all("timestamp" in s for s in trace["steps"])
    assert trace["steps"][0]["timestamp"] == "2024-02-01T09:00:01Z"


def test_generic_mapping_validation(custom_mapping_fixture: dict) -> None:
    """Test mapping validation (unmappable fields)."""
    adapter = GenericAdapter(custom_mapping_fixture)

    # Create incomplete data
    incomplete = {
        "execution": {
            "run_id": "test-001"
            # Missing input_query, model_name, events
        }
    }

    warnings = adapter.validate_mapping(incomplete)
    assert len(warnings) > 0
    assert any("user_prompt" in w or "input_query" in w for w in warnings)


def test_generic_invalid_mapping_config() -> None:
    """Test error handling for invalid mapping config."""
    # Missing required fields
    invalid_mapping = {
        "task_id": "id"
        # Missing user_prompt, model_version, steps_path
    }

    with pytest.raises(ValueError, match="Missing required mapping"):
        GenericAdapter(invalid_mapping)
