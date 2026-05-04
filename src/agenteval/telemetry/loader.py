from __future__ import annotations

import json
from pathlib import Path

from .models import SpanRecord, TraceEnvelope

_REQUIRED_TRACE_KEYS = ("trace_id", "journey", "root_span_id", "spans")
_REQUIRED_SPAN_KEYS = ("span_id", "name", "service", "kind", "start_ms", "end_ms")
_SPAN_STR_FIELDS = ("span_id", "name", "service", "kind")
_SPAN_INT_FIELDS = ("start_ms", "end_ms")


def _validate_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("trace file must contain a JSON object at the top level")
    for key in _REQUIRED_TRACE_KEYS:
        if key not in payload:
            raise ValueError(f"trace missing required field: '{key}'")
    if not isinstance(payload["spans"], list):
        raise ValueError("trace field 'spans' must be a list")


def _validate_span(span: object, index: int) -> None:
    if not isinstance(span, dict):
        raise ValueError(f"spans[{index}] must be a JSON object")
    for key in _REQUIRED_SPAN_KEYS:
        if key not in span:
            raise ValueError(f"spans[{index}] missing required field: '{key}'")
    for key in _SPAN_STR_FIELDS:
        if not isinstance(span[key], str):
            raise ValueError(
                f"spans[{index}].{key} must be a string, got {type(span[key]).__name__}"
            )
    for key in _SPAN_INT_FIELDS:
        if not isinstance(span[key], int):
            raise ValueError(
                f"spans[{index}].{key} must be an integer, got {type(span[key]).__name__}"
            )


def load_trace(path: str | Path) -> TraceEnvelope:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"trace file is not valid JSON: {exc}") from exc

    _validate_payload(payload)
    spans = []
    for i, span_data in enumerate(payload["spans"]):
        _validate_span(span_data, i)
        spans.append(
            SpanRecord(
                span_id=span_data["span_id"],
                parent_span_id=span_data.get("parent_span_id"),
                name=span_data["name"],
                service=span_data["service"],
                kind=span_data["kind"],
                start_ms=span_data["start_ms"],
                end_ms=span_data["end_ms"],
                attributes=span_data.get("attributes", {}),
            )
        )

    return TraceEnvelope(
        trace_id=payload["trace_id"],
        journey=payload["journey"],
        root_span_id=payload["root_span_id"],
        spans=spans,
    )
