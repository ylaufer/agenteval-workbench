"""Run comparison engine for AgentEval.

Compares two evaluation runs by computing per-case and per-dimension score
deltas, classifying changes, and returning a validated ComparisonResult.
"""

from __future__ import annotations

import argparse
import json
import math
import secrets
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence, cast

import jsonschema  # type: ignore[import-untyped]

from agenteval.dataset.validator import _get_repo_root
from agenteval.core.runs import get_run, get_run_results


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseDelta:
    case_id: str
    status: Literal["improved", "regressed", "unchanged", "new", "removed"]
    overall_score_a: float | None = None
    overall_score_b: float | None = None
    overall_delta: float | None = None
    dimension_deltas: dict[str, float | None] = field(default_factory=dict)
    primary_failure_a: str | None = None
    primary_failure_b: str | None = None


@dataclass(frozen=True)
class DimensionDelta:
    dimension: str
    mean_score_a: float | None = None
    mean_score_b: float | None = None
    mean_delta: float | None = None
    std_delta: float | None = None
    cases_improved: int = 0
    cases_regressed: int = 0
    cases_unchanged: int = 0


@dataclass(frozen=True)
class ComparisonSummary:
    total_cases_compared: int
    cases_improved: int
    cases_regressed: int
    cases_unchanged: int
    cases_new: int
    cases_removed: int
    overall_score_delta: float | None
    net_quality_change: Literal["improved", "regressed", "unchanged", "insufficient_data"]
    new_failure_types: list[str]
    resolved_failure_types: list[str]


@dataclass(frozen=True)
class ComparisonResult:
    comparison_id: str
    run_a: str
    run_b: str
    timestamp: str
    summary: ComparisonSummary
    dimension_deltas: list[DimensionDelta]
    case_deltas: list[CaseDelta]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_scale_max(scale: str) -> float:
    """Parse 'min-max' scale string and return max as float. E.g. '0-2' → 2.0."""
    try:
        return float(scale.split("-")[1])
    except (IndexError, ValueError):
        return 2.0  # safe default for rubric dimensions


def _normalize_score(raw: int, scale_max: float) -> float:
    """Normalize a raw integer score to [0.0, 1.0]."""
    if scale_max == 0:
        return 0.0
    return raw / scale_max


def _compute_overall_score(dimensions: dict[str, Any]) -> float | None:
    """Weighted average of normalized per-dimension scores.

    Dimensions with null scores are excluded. Returns None if no dimension
    is scored.
    """
    weighted_sum = 0.0
    total_weight = 0.0
    for dim_data in dimensions.values():
        raw = dim_data.get("score")
        if raw is None:
            continue
        weight = float(dim_data.get("weight", 1.0))
        scale_max = _parse_scale_max(dim_data.get("scale", "0-2"))
        weighted_sum += _normalize_score(int(raw), scale_max) * weight
        total_weight += weight
    if total_weight == 0.0:
        return None
    return weighted_sum / total_weight


def classify_change(
    score_a: float | None,
    score_b: float | None,
) -> Literal["improved", "regressed", "unchanged"]:
    """Classify the type of change between two normalized overall scores."""
    if score_a is None and score_b is None:
        return "unchanged"
    if score_a is None or score_b is None:
        return "unchanged"
    delta = round(score_b - score_a, 6)
    if delta > 0:
        return "improved"
    if delta < 0:
        return "regressed"
    return "unchanged"


def _generate_comparison_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = secrets.token_hex(2)
    return f"comp_{ts}_{suffix}"


def _index_results(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index per-case evaluation dicts by case_id."""
    return {r["case_id"]: r for r in results if "case_id" in r}


def _build_case_deltas(
    results_a: list[dict[str, Any]],
    results_b: list[dict[str, Any]],
) -> list[CaseDelta]:
    """Align cases by case_id and compute per-case deltas."""
    index_a = _index_results(results_a)
    index_b = _index_results(results_b)
    all_ids = sorted(set(index_a) | set(index_b))

    deltas: list[CaseDelta] = []
    for case_id in all_ids:
        rec_a = index_a.get(case_id)
        rec_b = index_b.get(case_id)

        if rec_a is None:
            # New case — only in B (rec_b must exist since case_id ∈ index_b)
            rec_b_nn = cast("dict[str, Any]", rec_b)
            overall_b = _compute_overall_score(rec_b_nn.get("dimensions", {}))
            deltas.append(
                CaseDelta(
                    case_id=case_id,
                    status="new",
                    overall_score_b=overall_b,
                    primary_failure_b=rec_b_nn.get("primary_failure"),
                )
            )
            continue

        if rec_b is None:
            # Removed case — only in A
            overall_a = _compute_overall_score(rec_a.get("dimensions", {}))
            deltas.append(
                CaseDelta(
                    case_id=case_id,
                    status="removed",
                    overall_score_a=overall_a,
                    primary_failure_a=rec_a.get("primary_failure"),
                )
            )
            continue

        dims_a = rec_a.get("dimensions", {})
        dims_b = rec_b.get("dimensions", {})
        overall_a = _compute_overall_score(dims_a)
        overall_b = _compute_overall_score(dims_b)

        if overall_a is not None and overall_b is not None:
            overall_delta: float | None = round(overall_b - overall_a, 6)
        else:
            overall_delta = None

        status = classify_change(overall_a, overall_b)

        # Per-dimension deltas
        all_dims = sorted(set(dims_a) | set(dims_b))
        dim_deltas: dict[str, float | None] = {}
        for dim_name in all_dims:
            da = dims_a.get(dim_name)
            db = dims_b.get(dim_name)
            raw_a = da.get("score") if da else None
            raw_b = db.get("score") if db else None
            if raw_a is not None and raw_b is not None:
                sm_a = _parse_scale_max(da.get("scale", "0-2"))
                sm_b = _parse_scale_max(db.get("scale", "0-2"))
                norm_a = _normalize_score(int(raw_a), sm_a)
                norm_b = _normalize_score(int(raw_b), sm_b)
                dim_deltas[dim_name] = round(norm_b - norm_a, 6)
            else:
                dim_deltas[dim_name] = None

        deltas.append(
            CaseDelta(
                case_id=case_id,
                status=status,
                overall_score_a=overall_a,
                overall_score_b=overall_b,
                overall_delta=overall_delta,
                dimension_deltas=dim_deltas,
                primary_failure_a=rec_a.get("primary_failure"),
                primary_failure_b=rec_b.get("primary_failure"),
            )
        )

    # Sort by abs(overall_delta) descending, new/removed last
    def _sort_key(cd: CaseDelta) -> float:
        if cd.overall_delta is not None:
            return -abs(cd.overall_delta)
        return 1.0  # new/removed go to end

    deltas.sort(key=_sort_key)
    return deltas


def _build_dimension_deltas(case_deltas: list[CaseDelta]) -> list[DimensionDelta]:
    """Aggregate per-dimension stats across all comparable case deltas."""
    # Collect all dimension names from comparable cases
    dim_names: set[str] = set()
    for cd in case_deltas:
        if cd.status in ("new", "removed"):
            continue
        dim_names.update(cd.dimension_deltas.keys())

    result: list[DimensionDelta] = []
    for dim in sorted(dim_names):
        improved = regressed = unchanged = 0

        for cd in case_deltas:
            if cd.status in ("new", "removed"):
                continue
            delta = cd.dimension_deltas.get(dim)
            if delta is None:
                continue
            # Recover individual scores if available
            if delta > 0:
                improved += 1
            elif delta < 0:
                regressed += 1
            else:
                unchanged += 1

        # Compute mean scores across all comparable cases for this dimension
        for cd in case_deltas:
            if cd.status in ("new", "removed"):
                continue
            delta = cd.dimension_deltas.get(dim)
            if delta is None:
                continue
            # We only have the delta; compute means from overall context
            # Store per-case scores from case_deltas for aggregation

        # Second pass: gather individual dimension scores from raw case data
        # (available only as deltas; compute mean_a/mean_b from available values)
        score_a_vals: list[float] = []
        score_b_vals: list[float] = []
        deltas_list: list[float] = []
        for cd in case_deltas:
            if cd.status in ("new", "removed"):
                continue
            delta = cd.dimension_deltas.get(dim)
            if delta is None:
                continue
            deltas_list.append(delta)
            if cd.overall_score_a is not None:
                score_a_vals.append(cd.overall_score_a)
            if cd.overall_score_b is not None:
                score_b_vals.append(cd.overall_score_b)

        mean_delta = (sum(deltas_list) / len(deltas_list)) if deltas_list else None

        # Std dev of deltas
        std_delta: float | None = None
        if len(deltas_list) >= 2:
            mean_d = mean_delta or 0.0
            variance = sum((d - mean_d) ** 2 for d in deltas_list) / len(deltas_list)
            std_delta = math.sqrt(variance)

        result.append(
            DimensionDelta(
                dimension=dim,
                mean_delta=round(mean_delta, 6) if mean_delta is not None else None,
                std_delta=round(std_delta, 6) if std_delta is not None else None,
                cases_improved=improved,
                cases_regressed=regressed,
                cases_unchanged=unchanged,
            )
        )

    return result


def _build_summary(
    case_deltas: list[CaseDelta],
    run_a_id: str,
    run_b_id: str,
) -> ComparisonSummary:
    comparable = [cd for cd in case_deltas if cd.status not in ("new", "removed")]
    new_cases = [cd for cd in case_deltas if cd.status == "new"]
    removed_cases = [cd for cd in case_deltas if cd.status == "removed"]

    improved = sum(1 for cd in comparable if cd.status == "improved")
    regressed = sum(1 for cd in comparable if cd.status == "regressed")
    unchanged = sum(1 for cd in comparable if cd.status == "unchanged")

    scored_deltas = [cd.overall_delta for cd in comparable if cd.overall_delta is not None]
    overall_score_delta: float | None = None
    if scored_deltas:
        overall_score_delta = round(sum(scored_deltas) / len(scored_deltas), 6)

    net: Literal["improved", "regressed", "unchanged", "insufficient_data"]
    if overall_score_delta is None:
        net = "insufficient_data"
    elif overall_score_delta > 0:
        net = "improved"
    elif overall_score_delta < 0:
        net = "regressed"
    else:
        net = "unchanged"

    # Failure type analysis
    failures_a = {
        cd.primary_failure_a for cd in case_deltas if cd.primary_failure_a and cd.status != "new"
    }
    failures_b = {
        cd.primary_failure_b
        for cd in case_deltas
        if cd.primary_failure_b and cd.status != "removed"
    }
    new_failure_types = sorted(failures_b - failures_a)
    resolved_failure_types = sorted(failures_a - failures_b)

    return ComparisonSummary(
        total_cases_compared=len(comparable),
        cases_improved=improved,
        cases_regressed=regressed,
        cases_unchanged=unchanged,
        cases_new=len(new_cases),
        cases_removed=len(removed_cases),
        overall_score_delta=overall_score_delta,
        net_quality_change=net,
        new_failure_types=new_failure_types,
        resolved_failure_types=resolved_failure_types,
    )


def _validate_result(result: ComparisonResult, repo_root: Path) -> None:
    """Validate ComparisonResult against comparison_schema.json."""
    schema_path = repo_root / "schemas" / "comparison_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = asdict(result)
    jsonschema.validate(instance=data, schema=schema)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compare_runs(
    run_a_id: str,
    run_b_id: str,
    repo_root: Path | None = None,
) -> ComparisonResult:
    """Compare two evaluation runs and return a structured diff.

    Raises FileNotFoundError if either run directory is missing.
    Raises ValueError if run data is malformed.
    Raises jsonschema.ValidationError if the result fails schema validation.
    """
    if repo_root is None:
        repo_root = _get_repo_root()

    # Verify both runs exist
    if get_run(run_a_id) is None:
        raise FileNotFoundError(f"Run '{run_a_id}' not found")
    if get_run(run_b_id) is None:
        raise FileNotFoundError(f"Run '{run_b_id}' not found")

    results_a = get_run_results(run_a_id)
    results_b = get_run_results(run_b_id)

    case_deltas = _build_case_deltas(results_a, results_b)
    dimension_deltas = _build_dimension_deltas(case_deltas)
    summary = _build_summary(case_deltas, run_a_id, run_b_id)

    result = ComparisonResult(
        comparison_id=_generate_comparison_id(),
        run_a=run_a_id,
        run_b=run_b_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        dimension_deltas=dimension_deltas,
        case_deltas=case_deltas,
    )
    _validate_result(result, repo_root)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_DELTA_ARROW = {True: "▲", False: "▼", None: "–"}


def _fmt_delta(delta: float | None) -> str:
    if delta is None:
        return "  n/a  "
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:+.3f}"


def _delta_arrow(delta: float | None) -> str:
    if delta is None or abs(delta) < 1e-9:
        return "–"
    return "▲" if delta > 0 else "▼"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agenteval-compare",
        description="Compare two AgentEval evaluation runs.",
    )
    group = parser.add_argument_group("run selection")
    group.add_argument("--run-a", dest="run_a", metavar="RUN_ID", help="Baseline run ID")
    group.add_argument("--run-b", dest="run_b", metavar="RUN_ID", help="Current run ID")
    group.add_argument("--baseline", metavar="RUN_ID", help="Alias for --run-a")
    group.add_argument("--current", metavar="RUN_ID", help="Alias for --run-b")
    parser.add_argument("--output-json", metavar="PATH", help="Write full comparison JSON to file")
    args = parser.parse_args(argv)

    run_a = args.run_a or args.baseline
    run_b = args.run_b or args.current

    if not run_a or not run_b:
        parser.error("Provide --run-a/--run-b or --baseline/--current")

    try:
        result = compare_runs(run_a, run_b)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (ValueError, jsonschema.ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    s = result.summary
    run_a_count = sum(1 for cd in result.case_deltas if cd.status != "new")
    run_b_count = sum(1 for cd in result.case_deltas if cd.status != "removed")

    print(f"Run A : {result.run_a}  ({run_a_count} cases)")
    print(f"Run B : {result.run_b}  ({run_b_count} cases)")
    print()
    print("Summary")
    delta_str = f"{_fmt_delta(s.overall_score_delta)} {_delta_arrow(s.overall_score_delta)}"
    print(f"  Overall score delta : {delta_str}  ({s.net_quality_change})")
    print(f"  Cases improved      : {s.cases_improved}")
    print(f"  Cases regressed     : {s.cases_regressed}")
    print(f"  Cases unchanged     : {s.cases_unchanged}")
    if s.cases_new:
        print(f"  Cases new           : {s.cases_new}")
    if s.cases_removed:
        print(f"  Cases removed       : {s.cases_removed}")
    nft = ", ".join(s.new_failure_types) if s.new_failure_types else "(none)"
    rft = ", ".join(s.resolved_failure_types) if s.resolved_failure_types else "(none)"
    print(f"  New failure types   : {nft}")
    print(f"  Resolved failures   : {rft}")

    if result.dimension_deltas:
        print()
        print("Dimension Deltas")
        header = f"  {'Dimension':<22} {'Delta':>8}  {'Impr':>4}  {'Regr':>4}  {'Same':>4}"
        print(header)
        print("  " + "─" * (len(header) - 2))
        for dd in result.dimension_deltas:
            arrow = _delta_arrow(dd.mean_delta)
            d_str = f"{_fmt_delta(dd.mean_delta)} {arrow}"
            print(
                f"  {dd.dimension:<22} {d_str:>12}  {dd.cases_improved:>4}  "
                f"{dd.cases_regressed:>4}  {dd.cases_unchanged:>4}"
            )

    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
        print(f"\nComparison JSON written to {out}")

    return 0
