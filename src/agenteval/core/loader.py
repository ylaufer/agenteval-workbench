from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, cast

import jsonschema

from agenteval.dataset.validator import _get_repo_root, _load_json, _safe_resolve_within
from .types import Rubric, RubricDimension


def _load_json_schema(schema_path: Path) -> Dict[str, Any]:
    schema_obj = _load_json(schema_path)
    if not isinstance(schema_obj, dict):
        msg = f"Schema at {schema_path} is not a JSON object"
        raise TypeError(msg)
    return cast(Dict[str, Any], schema_obj)


def load_rubric(
    rubric_path: Path | None = None,
    schema_path: Path | None = None,
) -> Rubric:
    """
    Load a rubric configuration, validate it against `schemas/rubric_schema.json`,
    and return a typed `Rubric` object.

    The default rubric path is `rubrics/v1_agent_general.json` at repo root.
    """
    repo_root = _get_repo_root()

    if rubric_path is None:
        rubric_path = repo_root / "rubrics" / "v1_agent_general.json"
    if schema_path is None:
        schema_path = repo_root / "schemas" / "rubric_schema.json"

    rubric_path = _safe_resolve_within(repo_root, rubric_path)
    schema_path = _safe_resolve_within(repo_root, schema_path)

    rubric_obj = _load_json(rubric_path)
    if not isinstance(rubric_obj, dict):
        msg = f"Rubric at {rubric_path} is not a JSON object"
        raise TypeError(msg)

    schema = _load_json_schema(schema_path)
    jsonschema.validate(instance=rubric_obj, schema=schema)

    return _rubric_from_dict(rubric_obj)


def _rubric_from_dict(obj: Dict[str, Any]) -> Rubric:
    version = cast(str, obj["version"])
    name = cast(str | None, obj.get("name"))

    security = cast(Dict[str, Any] | None, obj.get("security"))
    redact_patterns: Tuple[str, ...]
    if security is None:
        redact_patterns = ()
    else:
        patterns = security.get("redact_patterns", [])
        if not isinstance(patterns, list):
            msg = "security.redact_patterns must be a list of strings"
            raise TypeError(msg)
        redact_patterns = tuple(str(p) for p in patterns)

    dimensions_raw = cast(Any, obj["dimensions"])
    if not isinstance(dimensions_raw, list):
        msg = "dimensions must be a list"
        raise TypeError(msg)

    dimensions: list[RubricDimension] = []
    for dim_obj in dimensions_raw:
        if not isinstance(dim_obj, dict):
            msg = "each dimension must be an object"
            raise TypeError(msg)

        name_value = str(dim_obj["name"])
        title_value = cast(str | None, dim_obj.get("title"))
        scale_value = str(dim_obj["scale"])
        weight_value = float(dim_obj.get("weight", 1.0))
        description_value = str(dim_obj["description"])

        scoring_guide_obj = cast(Dict[str, Any], dim_obj["scoring_guide"])
        scoring_guide: Dict[str, str] = {
            key: str(val) for key, val in scoring_guide_obj.items()
        }

        evidence_required_value = bool(dim_obj.get("evidence_required", True))

        dimensions.append(
            RubricDimension(
                name=name_value,
                title=title_value,
                scale=scale_value,
                weight=weight_value,
                description=description_value,
                scoring_guide=scoring_guide,
                evidence_required=evidence_required_value,
            )
        )

    return Rubric(
        version=version,
        name=name,
        security_redact_patterns=tuple(redact_patterns),
        dimensions=tuple(dimensions),
    )


def load_trace(
    trace_path: Path,
    schema_path: Path | None = None,
) -> Dict[str, Any]:
    """
    Load a single trace.json file, validate it against `schemas/trace_schema.json`,
    and return the raw JSON object.
    """
    repo_root = _get_repo_root()

    if schema_path is None:
        schema_path = repo_root / "schemas" / "trace_schema.json"

    trace_path = _safe_resolve_within(repo_root, trace_path)
    schema_path = _safe_resolve_within(repo_root, schema_path)

    schema = _load_json_schema(schema_path)
    trace_obj = _load_json(trace_path)
    jsonschema.validate(instance=trace_obj, schema=schema)

    if not isinstance(trace_obj, dict):
        msg = f"Trace at {trace_path} is not a JSON object"
        raise TypeError(msg)
    return cast(Dict[str, Any], trace_obj)

