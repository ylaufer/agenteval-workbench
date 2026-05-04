from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from .models import TraceEnvelope, SpanRecord


def load_redaction_rules(path: str | Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def _redact_value(text: str, rules: list[dict[str, Any]]) -> str:
    result = text
    for rule in rules:
        regex = rule.get("regex")
        if regex:
            result = re.sub(regex, rule["replacement"], result)
    return result


def _walk(value: Any, rules: list[dict[str, Any]], _path: str = "") -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            full_path = f"{_path}.{k}" if _path else k
            direct = next(
                (
                    r
                    for r in rules
                    if full_path in r.get("path_patterns", [])
                    or f"attributes.{full_path}" in r.get("path_patterns", [])
                ),
                None,
            )
            if direct:
                out[k] = direct["replacement"]
            else:
                out[k] = _walk(v, rules, full_path)
        return out
    if isinstance(value, list):
        return [_walk(v, rules, _path) for v in value]
    if isinstance(value, str):
        return _redact_value(value, rules)
    return value


def redact_trace(trace: TraceEnvelope, rules_config: dict[str, Any]) -> TraceEnvelope:
    rules = rules_config.get("redaction_rules", [])
    if not rules:
        raise ValueError(
            "redact_trace requires at least one redaction rule; "
            "refusing to process trace without a valid redaction config"
        )
    cloned = copy.deepcopy(trace)
    cloned.spans = [
        SpanRecord(
            span_id=s.span_id,
            parent_span_id=s.parent_span_id,
            name=s.name,
            service=s.service,
            kind=s.kind,
            start_ms=s.start_ms,
            end_ms=s.end_ms,
            attributes=_walk(s.attributes, rules),
        )
        for s in cloned.spans
    ]
    return cloned
