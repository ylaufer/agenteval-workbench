from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]


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


def load_invariants(path: str | Path) -> dict[str, Any]:
    config = cast(dict[str, Any], yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    validate_invariants(config)
    return config
