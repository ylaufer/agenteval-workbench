from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within
from .loader import load_rubric


Numeric = float


@dataclass(frozen=True)
class _DimensionStats:
    name: str
    scale_min: Numeric
    scale_max: Numeric
    weight: Numeric
    num_scored: int
    num_unscored: int
    mean_score: Numeric | None
    distribution: Mapping[str, int]


@dataclass(frozen=True)
class _CaseAggregate:
    case_id: str
    overall_score: Numeric | None
    primary_failure: str | None
    severity: str | None


def _parse_scale(scale: str) -> Tuple[Numeric, Numeric]:
    """
    Parse a scale like '0-2' or '1-5' into (min, max).
    """
    try:
        parts = scale.split("-")
        if len(parts) != 2:
            raise ValueError(scale)
        low = float(parts[0])
        high = float(parts[1])
        if high <= low:
            raise ValueError(scale)
        return low, high
    except Exception as exc:  # noqa: BLE001
        msg = f"Unsupported scale format: {scale!r}"
        raise ValueError(msg) from exc


def _iter_evaluation_files(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.iterdir(), key=lambda p: p.name):
        if path.is_file() and path.name.endswith(".evaluation.json"):
            yield path


def _load_evaluation(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def _collect_dimension_stats(
    evaluations: Sequence[Mapping[str, Any]],
    rubric_info: Mapping[str, Tuple[str, Numeric]],
) -> Dict[str, _DimensionStats]:
    distributions: Dict[str, Counter[str]] = defaultdict(Counter)
    totals: Dict[str, Numeric] = defaultdict(float)
    num_scored: Dict[str, int] = defaultdict(int)
    num_unscored: Dict[str, int] = defaultdict(int)

    for eval_obj in evaluations:
        dims = eval_obj.get("dimensions")
        if not isinstance(dims, Mapping):
            continue
        for dim_name, dim_val in dims.items():
            if dim_name not in rubric_info:
                continue
            scale_str, weight = rubric_info[dim_name]
            _ = weight  # weight used later for overall scores; stats are unweighted.
            score = dim_val.get("score") if isinstance(dim_val, Mapping) else None
            if isinstance(score, (int, float)):
                score_str = str(int(score))
                distributions[dim_name][score_str] += 1
                totals[dim_name] += float(score)
                num_scored[dim_name] += 1
            else:
                num_unscored[dim_name] += 1

    stats: Dict[str, _DimensionStats] = {}
    for dim_name, (scale_str, weight) in rubric_info.items():
        scale_min, scale_max = _parse_scale(scale_str)
        scored = num_scored.get(dim_name, 0)
        mean_score: Numeric | None
        if scored:
            mean_score = totals[dim_name] / scored
        else:
            mean_score = None
        stats[dim_name] = _DimensionStats(
            name=dim_name,
            scale_min=scale_min,
            scale_max=scale_max,
            weight=weight,
            num_scored=scored,
            num_unscored=num_unscored.get(dim_name, 0),
            mean_score=mean_score,
            distribution=dict(sorted(distributions[dim_name].items())),
        )
    return stats


def _compute_case_overall_scores(
    evaluations: Sequence[Mapping[str, Any]],
    rubric_info: Mapping[str, Tuple[str, Numeric]],
) -> Sequence[_CaseAggregate]:
    aggregates: list[_CaseAggregate] = []
    for eval_obj in evaluations:
        case_id = str(eval_obj.get("case_id", ""))
        dims = eval_obj.get("dimensions")
        if not isinstance(dims, Mapping):
            overall_score: Numeric | None = None
        else:
            weighted_sum: Numeric = 0.0
            total_weight: Numeric = 0.0
            for dim_name, dim_val in dims.items():
                if dim_name not in rubric_info:
                    continue
                scale_str, weight = rubric_info[dim_name]
                scale_min, scale_max = _parse_scale(scale_str)
                score = dim_val.get("score") if isinstance(dim_val, Mapping) else None
                if not isinstance(score, (int, float)):
                    continue
                normalized = (float(score) - scale_min) / (scale_max - scale_min)
                weighted_sum += normalized * weight
                total_weight += weight
            if total_weight > 0:
                overall_score = weighted_sum / total_weight
            else:
                overall_score = None

        primary_failure = eval_obj.get("primary_failure")
        severity = eval_obj.get("severity")
        aggregates.append(
            _CaseAggregate(
                case_id=case_id,
                overall_score=overall_score,
                primary_failure=str(primary_failure) if primary_failure else None,
                severity=str(severity) if severity else None,
            )
        )
    return aggregates


def _summarize_failures(
    evaluations: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    primary_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()

    for eval_obj in evaluations:
        primary = eval_obj.get("primary_failure")
        if isinstance(primary, str) and primary:
            primary_counts[primary] += 1
        severity = eval_obj.get("severity")
        if isinstance(severity, str) and severity:
            severity_counts[severity] += 1

    return {
        "primary_failure_counts": dict(sorted(primary_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
    }


def _generate_recommendations(
    dimension_stats: Mapping[str, _DimensionStats],
    failure_summary: Mapping[str, Any],
) -> list[str]:
    recommendations: list[str] = []

    primary_counts = failure_summary.get("primary_failure_counts", {})
    if isinstance(primary_counts, Mapping):
        sorted_failures = sorted(
            primary_counts.items(), key=lambda kv: kv[1], reverse=True
        )
        for failure, count in sorted_failures[:3]:
            recommendations.append(
                f"Investigate recurring failure type '{failure}' "
                f"(observed in {count} case(s)); design targeted test cases and mitigations."
            )

    for dim_name, stats in dimension_stats.items():
        if stats.mean_score is None:
            continue
        if stats.scale_max <= stats.scale_min:
            continue
        normalized = (stats.mean_score - stats.scale_min) / (
            stats.scale_max - stats.scale_min
        )
        if normalized < 0.75:
            recommendations.append(
                f"Focus on dimension '{dim_name}': average score {stats.mean_score:.2f} "
                f"out of {stats.scale_max:.0f}; prioritize improvements and clearer "
                "guidance for evaluators on this dimension."
            )

    if not recommendations:
        recommendations.append(
            "Scores are near the top of each scale across dimensions; consider expanding "
            "the benchmark with harder cases to better differentiate model behavior."
        )

    return recommendations


def _build_json_report(
    evaluations: Sequence[Mapping[str, Any]],
    dimension_stats: Mapping[str, _DimensionStats],
    case_aggregates: Sequence[_CaseAggregate],
    failure_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    num_cases = len(evaluations)
    num_scored_cases = sum(
        1 for agg in case_aggregates if agg.overall_score is not None
    )

    dim_section: Dict[str, Any] = {}
    for name, stats in sorted(dimension_stats.items()):
        dim_section[name] = {
            "scale_min": stats.scale_min,
            "scale_max": stats.scale_max,
            "weight": stats.weight,
            "num_scored": stats.num_scored,
            "num_unscored": stats.num_unscored,
            "mean_score": stats.mean_score,
            "distribution": stats.distribution,
        }

    sorted_cases = sorted(
        case_aggregates,
        key=lambda c: (c.overall_score is None, c.overall_score),
    )
    failed_cases: list[Dict[str, Any]] = []
    for agg in sorted_cases:
        if agg.overall_score is None:
            continue
        if agg.overall_score >= 0.9:
            continue
        failed_cases.append(
            {
                "case_id": agg.case_id,
                "overall_score_normalized": round(agg.overall_score, 3),
                "primary_failure": agg.primary_failure,
                "severity": agg.severity,
            }
        )

    recommendations = _generate_recommendations(dimension_stats, failure_summary)

    return {
        "summary": {
            "num_cases": num_cases,
            "num_scored_cases": num_scored_cases,
        },
        "dimensions": dim_section,
        "failure_summary": failure_summary,
        "failed_cases": failed_cases,
        "recommendations": recommendations,
    }


def _write_json(path: Path, obj: Mapping[str, Any]) -> None:
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def _write_markdown(
    path: Path,
    json_report: Mapping[str, Any],
) -> None:
    summary = json_report.get("summary", {})
    dimensions = json_report.get("dimensions", {})
    failure_summary = json_report.get("failure_summary", {})
    failed_cases = json_report.get("failed_cases", [])
    recommendations = json_report.get("recommendations", [])

    lines: list[str] = []
    lines.append("# Evaluation Summary Report")
    lines.append("")
    lines.append("## Summary metrics")
    lines.append("")
    num_cases = summary.get("num_cases", 0)
    num_scored_cases = summary.get("num_scored_cases", 0)
    lines.append(f"- Total cases: {num_cases}")
    lines.append(f"- Cases with overall scores: {num_scored_cases}")
    lines.append("")

    lines.append("## Dimension-level breakdown")
    lines.append("")
    lines.append(
        "| Dimension | Scale | Weight | Scored / Unscored | Mean score | Distribution |"
    )
    lines.append(
        "|-----------|-------|--------|-------------------|------------|--------------|"
    )
    if isinstance(dimensions, Mapping):
        for name, payload in sorted(dimensions.items()):
            if not isinstance(payload, Mapping):
                continue
            scale_min = payload.get("scale_min", 0)
            scale_max = payload.get("scale_max", 0)
            weight = payload.get("weight", 0)
            num_scored = payload.get("num_scored", 0)
            num_unscored = payload.get("num_unscored", 0)
            mean_score = payload.get("mean_score")
            distribution = payload.get("distribution", {})
            if isinstance(distribution, Mapping):
                dist_str = ", ".join(
                    f"{score}: {count}" for score, count in sorted(distribution.items())
                )
            else:
                dist_str = ""
            if isinstance(mean_score, (int, float)):
                mean_str = f"{mean_score:.2f}"
            else:
                mean_str = "-"
            lines.append(
                f"| `{name}` | {scale_min}-{scale_max} | {weight} | "
                f"{num_scored} / {num_unscored} | {mean_str} | {dist_str} |"
            )
    lines.append("")

    lines.append("## Failure pattern summary")
    lines.append("")
    if isinstance(failure_summary, Mapping):
        primary = failure_summary.get("primary_failure_counts", {})
        if isinstance(primary, Mapping) and primary:
            lines.append("- Primary failures:")
            for failure, count in sorted(primary.items(), key=lambda kv: kv[1], reverse=True):
                lines.append(f"  - `{failure}`: {count}")
        severity_counts = failure_summary.get("severity_counts", {})
        if isinstance(severity_counts, Mapping) and severity_counts:
            lines.append("- Severity distribution:")
            for severity, count in sorted(severity_counts.items(), key=lambda kv: kv[1], reverse=True):
                lines.append(f"  - `{severity}`: {count}")
    lines.append("")

    lines.append("## Notable failed cases")
    lines.append("")
    lines.append("| Case ID | Overall score (0-1) | Primary failure | Severity |")
    lines.append("|---------|----------------------|-----------------|----------|")
    if isinstance(failed_cases, list):
        for case in failed_cases:
            if not isinstance(case, Mapping):
                continue
            cid = case.get("case_id", "")
            score = case.get("overall_score_normalized")
            score_str = f"{score:.3f}" if isinstance(score, (int, float)) else "-"
            primary = case.get("primary_failure") or ""
            severity = case.get("severity") or ""
            lines.append(
                f"| `{cid}` | {score_str} | {primary} | {severity} |"
            )
    lines.append("")

    lines.append("## Improvement recommendations")
    lines.append("")
    if isinstance(recommendations, Sequence) and recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append("- No specific recommendations; scores appear uniformly strong.")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = _get_repo_root()

    parser = argparse.ArgumentParser(
        prog="agenteval-eval-report",
        description=(
            "Aggregate filled evaluation templates and generate structured JSON and "
            "Markdown reports."
        ),
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(repo_root / "reports"),
        help="Directory containing case_XXX.evaluation.json files (default: reports/).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=str(repo_root / "reports" / "summary.evaluation.json"),
        help="Path to write aggregated JSON report (default: reports/summary.evaluation.json).",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=str(repo_root / "reports" / "summary.evaluation.md"),
        help="Path to write aggregated Markdown report (default: reports/summary.evaluation.md).",
    )
    parser.add_argument(
        "--rubric-path",
        type=str,
        default=str(repo_root / "rubrics" / "v1_agent_general.json"),
        help="Path to rubric config (JSON, default: rubrics/v1_agent_general.json).",
    )

    args = parser.parse_args(argv)

    input_dir = _safe_resolve_within(repo_root, Path(args.input_dir))
    output_json_path = _safe_resolve_within(repo_root, Path(args.output_json))
    output_md_path = _safe_resolve_within(repo_root, Path(args.output_md))
    rubric_path = _safe_resolve_within(repo_root, Path(args.rubric_path))

    if not input_dir.exists() or not input_dir.is_dir():
        msg = f"Input directory does not exist or is not a directory: {input_dir}"
        raise SystemExit(msg)

    rubric = load_rubric(rubric_path=rubric_path, schema_path=None)
    rubric_info: Dict[str, Tuple[str, float]] = {
        dim.name: (dim.scale, dim.weight) for dim in rubric.dimensions
    }

    evaluation_files = list(_iter_evaluation_files(input_dir))
    if not evaluation_files:
        msg = f"No *.evaluation.json files found in {input_dir}"
        raise SystemExit(msg)

    evaluations: list[Mapping[str, Any]] = []
    for path in evaluation_files:
        evaluations.append(_load_evaluation(path))

    dimension_stats = _collect_dimension_stats(evaluations, rubric_info)
    case_aggregates = _compute_case_overall_scores(evaluations, rubric_info)
    failure_summary = _summarize_failures(evaluations)

    json_report = _build_json_report(
        evaluations=evaluations,
        dimension_stats=dimension_stats,
        case_aggregates=case_aggregates,
        failure_summary=failure_summary,
    )

    _write_json(output_json_path, json_report)
    _write_markdown(output_md_path, json_report)

    print(
        f"Wrote aggregated reports to {output_json_path} and {output_md_path}.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

