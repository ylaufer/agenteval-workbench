from __future__ import annotations

from .models import ConformanceResult, TraceEnvelope


def evaluate_conformance(trace: TraceEnvelope, invariant_config: dict) -> ConformanceResult:
    failures: list[str] = []
    journey = trace.journey
    definitions = invariant_config.get("journeys", [])
    spec = next((j for j in definitions if j.get("name") == journey), None)
    if spec is None:
        return ConformanceResult(journey=journey, passed=False, failures=["no invariant spec found"], metrics={})

    names = [span.name for span in trace.spans]
    for required in spec.get("required_spans", []):
        if required not in names:
            failures.append(f"missing required span: {required}")
    for forbidden in spec.get("forbidden_spans", []):
        if forbidden in names:
            failures.append(f"forbidden span present: {forbidden}")

    max_total_duration_ms = spec.get("max_total_duration_ms")
    total_duration = max((s.end_ms for s in trace.spans), default=0) - min((s.start_ms for s in trace.spans), default=0)
    if max_total_duration_ms is not None and total_duration > max_total_duration_ms:
        failures.append("trace exceeds max total duration")

    max_depth = spec.get("max_depth")
    if max_depth is not None and len(trace.spans) > max_depth:
        failures.append("trace exceeds max depth budget")

    return ConformanceResult(
        journey=journey,
        passed=not failures,
        failures=failures,
        metrics={"span_count": len(trace.spans), "total_duration_ms": total_duration},
    )
