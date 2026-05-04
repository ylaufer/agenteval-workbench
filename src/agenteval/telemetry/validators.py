from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from .loader import load_trace
from .models import TraceEnvelope


def load_thresholds(path: str | Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def validate_trace_structure(trace: TraceEnvelope) -> list[str]:
    errors: list[str] = []
    seen = {span.span_id for span in trace.spans}
    if trace.root_span_id not in seen:
        errors.append("root span missing")
    for span in trace.spans:
        if span.parent_span_id and span.parent_span_id not in seen:
            errors.append(f"missing parent for {span.span_id}")
        if span.end_ms < span.start_ms:
            errors.append(f"negative duration for {span.span_id}")
    return errors


def validate_trace_semantics(trace: TraceEnvelope) -> list[str]:
    errors: list[str] = []
    for span in trace.spans:
        if not span.name:
            errors.append(f"span {span.span_id} missing name")
        if not span.service:
            errors.append(f"span {span.span_id} missing service")
        if not span.kind:
            errors.append(f"span {span.span_id} missing kind")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a local telemetry trace fixture.")
    parser.add_argument("trace", help="Path to a trace JSON fixture file")
    args = parser.parse_args()

    trace_path = Path(args.trace)
    if not trace_path.exists():
        print(f"error: trace file not found: {trace_path}", file=sys.stderr)
        sys.exit(1)

    trace = load_trace(trace_path)
    structural = validate_trace_structure(trace)
    semantic = validate_trace_semantics(trace)

    all_errors = structural + semantic
    if all_errors:
        for err in all_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)

    print(f"ok: {trace_path} — {len(trace.spans)} span(s), no issues")
