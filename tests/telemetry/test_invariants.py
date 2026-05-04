from pathlib import Path

import pytest

from agenteval.telemetry.invariants import load_invariants, validate_invariants


def test_load_invariants() -> None:
    config = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    assert config["journeys"][0]["name"] == "simple_rag_query"


def test_validate_invariants_valid() -> None:
    validate_invariants({"journeys": [{"name": "my_journey"}]})


def test_validate_invariants_not_a_dict() -> None:
    with pytest.raises(ValueError, match="must be a mapping"):
        validate_invariants([])  # type: ignore[arg-type]


def test_validate_invariants_missing_journeys() -> None:
    with pytest.raises(ValueError, match="missing required field: 'journeys'"):
        validate_invariants({})


def test_validate_invariants_journeys_not_list() -> None:
    with pytest.raises(ValueError, match="missing required field: 'journeys'"):
        validate_invariants({"journeys": "not-a-list"})


def test_validate_invariants_empty_journeys() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_invariants({"journeys": []})


def test_validate_invariants_journey_not_dict() -> None:
    with pytest.raises(ValueError, match=r"journeys\[0\] must be a mapping"):
        validate_invariants({"journeys": ["not-a-dict"]})


def test_validate_invariants_journey_missing_name() -> None:
    with pytest.raises(ValueError, match="missing required string field: 'name'"):
        validate_invariants({"journeys": [{"required_spans": []}]})


def test_validate_invariants_journey_empty_name() -> None:
    with pytest.raises(ValueError, match="missing required string field: 'name'"):
        validate_invariants({"journeys": [{"name": ""}]})
