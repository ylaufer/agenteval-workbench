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
    span_ids = [span.span_id for span in trace.spans]
    seen = set(span_ids)

    # Duplicate span IDs
    counts: dict[str, int] = {}
    for sid in span_ids:
        counts[sid] = counts.get(sid, 0) + 1
    for sid, count in counts.items():
        if count > 1:
            errors.append(f"duplicate span_id: {sid}")

    if trace.root_span_id not in seen:
        errors.append("root span missing")

    for span in trace.spans:
        # Self-referencing parent
        if span.parent_span_id == span.span_id:
            errors.append(f"self-parent span: {span.span_id}")
        elif span.parent_span_id and span.parent_span_id not in seen:
            errors.append(f"missing parent for {span.span_id}")
        if span.end_ms < span.start_ms:
            errors.append(f"negative duration for {span.span_id}")

    # BFS orphan detection from root
    if trace.root_span_id in seen:
        children: dict[str, list[str]] = {sid: [] for sid in seen}
        for span in trace.spans:
            if span.parent_span_id and span.parent_span_id in children:
                children[span.parent_span_id].append(span.span_id)
        reachable: set[str] = set()
        queue = [trace.root_span_id]
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(children.get(current, []))
        for sid in seen:
            if sid not in reachable:
                errors.append(f"unreachable span: {sid}")

    if thresholds:
        cfg = thresholds.get("thresholds", {})
        max_span_count = cfg.get("max_span_count_default")
        if max_span_count is not None and len(trace.spans) > max_span_count:
            errors.append(f"span count {len(trace.spans)} exceeds max_span_count_default {max_span_count}")

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
