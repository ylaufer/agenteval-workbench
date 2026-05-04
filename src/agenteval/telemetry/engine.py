from __future__ import annotations

from .models import ConformanceResult, TraceEnvelope


def evaluate_conformance(trace: TraceEnvelope, invariant_config: dict) -> ConformanceResult:
    failures: list[str] = []
    journey = trace.journey
    definitions = invariant_config.get("journeys", [])
    spec = next((j for j in definitions if j.get("name") == journey), None)
    if spec is None:
        return ConformanceResult(
            journey=journey,
            passed=False,
            failures=["no invariant spec found"],
            trace_id=trace.trace_id,
            metrics={},
        )

    names = [span.name for span in trace.spans]
    for required in spec.get("required_spans", []):
        if required not in names:
            failures.append(f"missing required span: {required}")
    for forbidden in spec.get("forbidden_spans", []):
        if forbidden in names:
            failures.append(f"forbidden span present: {forbidden}")

    required_order: list[str] = spec.get("required_order", [])
    if required_order:
        # Collect the index of the first occurrence of each ordered span
        order_positions: list[tuple[str, int]] = []
        for span_name in required_order:
            try:
                order_positions.append((span_name, names.index(span_name)))
            except ValueError:
                pass  # missing required spans already caught above
        for i in range(1, len(order_positions)):
            prev_name, prev_pos = order_positions[i - 1]
            curr_name, curr_pos = order_positions[i]
            if curr_pos < prev_pos:
                failures.append(f"span order violated: '{prev_name}' must precede '{curr_name}'")

    # Occurrence bounds
    span_counts: dict[str, int] = {}
    for name in names:
        span_counts[name] = span_counts.get(name, 0) + 1
    for span_name, min_count in spec.get("min_occurrences", {}).items():
        actual = span_counts.get(span_name, 0)
        if actual < min_count:
            failures.append(
                f"span '{span_name}' appears {actual} time(s), expected at least {min_count}"
            )
    for span_name, max_count in spec.get("max_occurrences", {}).items():
        actual = span_counts.get(span_name, 0)
        if actual > max_count:
            failures.append(
                f"span '{span_name}' appears {actual} time(s), expected at most {max_count}"
            )

    max_total_duration_ms = spec.get("max_total_duration_ms")
    total_duration = max((s.end_ms for s in trace.spans), default=0) - min(
        (s.start_ms for s in trace.spans), default=0
    )
    if max_total_duration_ms is not None and total_duration > max_total_duration_ms:
        failures.append("trace exceeds max total duration")

    max_span_count = spec.get("max_span_count")
    if max_span_count is not None and len(trace.spans) > max_span_count:
        failures.append(f"span count {len(trace.spans)} exceeds max_span_count {max_span_count}")

    return ConformanceResult(
        journey=journey,
        passed=not failures,
        failures=failures,
        trace_id=trace.trace_id,
        metrics={"span_count": len(trace.spans), "total_duration_ms": total_duration},
    )
