from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]


def _check_list_of_strings(value: object, field: str, index: int) -> None:
    if not isinstance(value, list):
        raise ValueError(f"journeys[{index}].{field} must be a list, got {type(value).__name__}")
    for j, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"journeys[{index}].{field}[{j}] must be a string, got {type(item).__name__}"
            )


def _check_dict_of_str_to_int(value: object, field: str, index: int) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"journeys[{index}].{field} must be a mapping, got {type(value).__name__}")
    for k, v in value.items():
        if not isinstance(k, str):
            raise ValueError(f"journeys[{index}].{field} keys must be strings")
        if not isinstance(v, int):
            raise ValueError(
                f"journeys[{index}].{field}['{k}'] must be an integer, got {type(v).__name__}"
            )


def validate_invariants(config: dict[str, Any]) -> None:
    """Raise ValueError if the invariants config is structurally invalid."""
    if not isinstance(config, dict):
        raise ValueError("invariants config must be a mapping")
    journeys = config.get("journeys")
    if not isinstance(journeys, list):
        raise ValueError("invariants config missing required field: 'journeys'")
    if not journeys:
        raise ValueError("invariants config 'journeys' must not be empty")
    for i, journey in enumerate(journeys):
        if not isinstance(journey, dict):
            raise ValueError(f"journeys[{i}] must be a mapping")
        if "name" not in journey or not isinstance(journey["name"], str) or not journey["name"]:
            raise ValueError(f"journeys[{i}] missing required string field: 'name'")
        for list_field in ("required_spans", "forbidden_spans", "required_order"):
            if list_field in journey:
                _check_list_of_strings(journey[list_field], list_field, i)
        for int_field in ("max_span_count", "max_total_duration_ms"):
            if int_field in journey:
                if not isinstance(journey[int_field], int):
                    raise ValueError(
                        f"journeys[{i}].{int_field} must be an integer, "
                        f"got {type(journey[int_field]).__name__}"
                    )
        for dict_field in ("min_occurrences", "max_occurrences"):
            if dict_field in journey:
                _check_dict_of_str_to_int(journey[dict_field], dict_field, i)


def load_invariants(path: str | Path) -> dict[str, Any]:
    config = cast(dict[str, Any], yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    validate_invariants(config)
    return config
