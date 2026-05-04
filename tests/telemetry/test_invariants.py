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


# --- list-of-strings fields ---

def test_validate_invariants_required_spans_not_list() -> None:
    with pytest.raises(ValueError, match="required_spans must be a list"):
        validate_invariants({"journeys": [{"name": "j", "required_spans": "not-a-list"}]})


def test_validate_invariants_required_spans_contains_non_string() -> None:
    with pytest.raises(ValueError, match="must be a string"):
        validate_invariants({"journeys": [{"name": "j", "required_spans": [123]}]})


def test_validate_invariants_forbidden_spans_not_list() -> None:
    with pytest.raises(ValueError, match="forbidden_spans must be a list"):
        validate_invariants({"journeys": [{"name": "j", "forbidden_spans": {}}]})


def test_validate_invariants_required_order_contains_non_string() -> None:
    with pytest.raises(ValueError, match="must be a string"):
        validate_invariants({"journeys": [{"name": "j", "required_order": ["ok", None]}]})


# --- integer fields ---

def test_validate_invariants_max_span_count_not_int() -> None:
    with pytest.raises(ValueError, match="max_span_count must be an integer"):
        validate_invariants({"journeys": [{"name": "j", "max_span_count": "six"}]})


def test_validate_invariants_max_total_duration_not_int() -> None:
    with pytest.raises(ValueError, match="max_total_duration_ms must be an integer"):
        validate_invariants({"journeys": [{"name": "j", "max_total_duration_ms": 2.5}]})


# --- occurrence bound fields ---

def test_validate_invariants_min_occurrences_not_dict() -> None:
    with pytest.raises(ValueError, match="min_occurrences must be a mapping"):
        validate_invariants({"journeys": [{"name": "j", "min_occurrences": [1, 2]}]})


def test_validate_invariants_max_occurrences_value_not_int() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        validate_invariants({"journeys": [{"name": "j", "max_occurrences": {"span.foo": "two"}}]})


def test_validate_invariants_occurrence_keys_not_strings() -> None:
    with pytest.raises(ValueError, match="keys must be strings"):
        validate_invariants({"journeys": [{"name": "j", "min_occurrences": {123: 1}}]})


def test_validate_invariants_full_valid_journey() -> None:
    validate_invariants({
        "journeys": [{
            "name": "j",
            "required_spans": ["a", "b"],
            "forbidden_spans": ["c"],
            "required_order": ["a", "b"],
            "min_occurrences": {"a": 1},
            "max_occurrences": {"b": 3},
            "max_span_count": 10,
            "max_total_duration_ms": 5000,
        }]
    })
