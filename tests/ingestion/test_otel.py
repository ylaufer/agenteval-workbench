"""Tests for OpenTelemetry adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.ingestion.otel import OTelAdapter


@pytest.fixture
def otel_trace_fixture() -> dict:
    """Load OTel trace fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "otel_trace.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_otel_adapter_can_handle(otel_trace_fixture: dict) -> None:
    """Test OTelAdapter.can_handle() with valid OTel trace."""
    adapter = OTelAdapter()
    assert adapter.can_handle(otel_trace_fixture)


def test_otel_adapter_can_handle_invalid() -> None:
    """Test OTelAdapter.can_handle() rejects invalid format."""
    adapter = OTelAdapter()
    assert not adapter.can_handle({"invalid": "data"})


def test_otel_adapter_convert(otel_trace_fixture: dict) -> None:
    """Test OTelAdapter.convert() produces valid trace."""
    adapter = OTelAdapter()
    trace = adapter.convert(otel_trace_fixture)

    # Check trace structure
    assert "steps" in trace
    assert len(trace["steps"]) == 3

    # Check step types (using "type" field, not "step_type")
    assert trace["steps"][0]["type"] == "thought"
    assert trace["steps"][1]["type"] == "tool_call"
    assert trace["steps"][2]["type"] == "thought"  # final answer is also internal span


def test_otel_nested_span_flattening(otel_trace_fixture: dict) -> None:
    """Test that nested spans are flattened correctly."""
    adapter = OTelAdapter()
    trace = adapter.convert(otel_trace_fixture)

    # Parent span should not have parent_event_id
    assert "parent_event_id" not in trace["steps"][0]

    # Child spans should reference parent (using step_id)
    assert trace["steps"][1]["parent_event_id"] == trace["steps"][0]["step_id"]
    assert trace["steps"][2]["parent_event_id"] == trace["steps"][0]["step_id"]


def test_otel_malformed_trace() -> None:
    """Test error handling for malformed OTel trace."""
    adapter = OTelAdapter()
    malformed = {"resourceSpans": [{"scopeSpans": [{"spans": [{}]}]}]}

    with pytest.raises(ValueError, match="missing required field"):
        adapter.convert(malformed)
