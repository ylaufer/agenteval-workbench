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


def validate_trace_structure(
    trace: TraceEnvelope,
    thresholds: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    seen = {span.span_id for span in trace.spans}

    if trace.root_span_id not in seen:
        errors.append("root span missing")

    for span in trace.spans:
        if span.parent_span_id and span.parent_span_id not in seen:
            errors.append(f"missing parent for {span.span_id}")
        if span.end_ms < span.start_ms:
            errors.append(f"negative duration for {span.span_id}")

    if thresholds:
        cfg = thresholds.get("thresholds", {})
        max_depth = cfg.get("max_depth_default")
        if max_depth is not None and len(trace.spans) > max_depth:
            errors.append(f"span count {len(trace.spans)} exceeds max_depth_default {max_depth}")

        max_duration = cfg.get("max_total_duration_ms_default")
        if max_duration is not None and trace.spans:
            total = max(s.end_ms for s in trace.spans) - min(s.start_ms for s in trace.spans)
            if total > max_duration:
                errors.append(
                    f"total duration {total}ms exceeds max_total_duration_ms_default {max_duration}ms"
                )

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
    parser.add_argument("--thresholds", help="Optional path to telemetry_thresholds.yaml")
    args = parser.parse_args()

    trace_path = Path(args.trace)
    if not trace_path.exists():
        print(f"error: trace file not found: {trace_path}", file=sys.stderr)
        sys.exit(1)

    thresholds = None
    if args.thresholds:
        thresholds_path = Path(args.thresholds)
        if not thresholds_path.exists():
            print(f"error: thresholds file not found: {thresholds_path}", file=sys.stderr)
            sys.exit(1)
        thresholds = load_thresholds(thresholds_path)

    trace = load_trace(trace_path)
    structural = validate_trace_structure(trace, thresholds)
    semantic = validate_trace_semantics(trace)

    all_errors = structural + semantic
    if all_errors:
        for err in all_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)

    print(f"ok: {trace_path} — {len(trace.spans)} span(s), no issues")
