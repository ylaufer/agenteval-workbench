from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within
from .loader import load_reviewer_scores_for_case, load_rubric
from .types import ReviewerScore


Numeric = float


def _compute_percent_agreement(
    scores_a: Sequence[int],
    scores_b: Sequence[int],
) -> Numeric:
    """Compute pairwise percent agreement between two score vectors."""
    if not scores_a:
        return 0.0
    agreed = sum(1 for a, b in zip(scores_a, scores_b) if a == b)
    return agreed / len(scores_a)


def _compute_cohens_kappa(
    scores_a: Sequence[int],
    scores_b: Sequence[int],
    scale_min: int,
    scale_max: int,
) -> Numeric | None:
    """
    Compute Cohen's Kappa for two raters on an ordinal scale.

    Returns None if the expected agreement is 1.0 (all items in one category).
    """
    n = len(scores_a)
    if n == 0:
        return None

    categories = list(range(scale_min, scale_max + 1))

    # Observed agreement
    observed = sum(1 for a, b in zip(scores_a, scores_b) if a == b) / n

    # Expected agreement under independence
    expected = 0.0
    for cat in categories:
        count_a = sum(1 for s in scores_a if s == cat)
        count_b = sum(1 for s in scores_b if s == cat)
        expected += (count_a / n) * (count_b / n)

    if expected >= 1.0:
        return None

    return (observed - expected) / (1.0 - expected)


def _interpret_kappa(kappa: Numeric | None) -> str:
    """Return a human-readable interpretation of a Kappa value."""
    if kappa is None:
        return "undefined"
    if kappa < 0.0:
        return "poor (less than chance)"
    if kappa < 0.21:
        return "slight"
    if kappa < 0.41:
        return "fair"
    if kappa < 0.61:
        return "moderate"
    if kappa < 0.81:
        return "substantial"
    return "almost perfect"


def _collect_case_ids_from_scores_dir(scores_dir: Path) -> List[str]:
    """Discover unique case IDs from score filenames in scores_dir."""
    case_ids: set[str] = set()
    if not scores_dir.exists() or not scores_dir.is_dir():
        return []
    for path in scores_dir.iterdir():
        if path.is_file() and path.name.endswith(".json"):
            # Format: case_001_alice.json -> case_001
            parts = path.stem.rsplit("_", 1)
            if len(parts) == 2:
                case_ids.add(parts[0])
    return sorted(case_ids)


def compute_calibration_report(
    case_ids: Sequence[str],
    scores_dir: Path,
    rubric_info: Mapping[str, Tuple[str, Numeric]],
) -> Dict[str, Any]:
    """
    Compute pairwise inter-reviewer agreement for all reviewer pairs.

    Returns a dict suitable for JSON serialization with per-dimension stats.
    """
    # Gather all reviewer scores keyed by (case_id, reviewer_id, dimension)
    all_scores: Dict[str, list[ReviewerScore]] = {}
    for case_id in case_ids:
        scores = load_reviewer_scores_for_case(case_id, scores_dir)
        if len(scores) >= 2:
            all_scores[case_id] = scores

    if not all_scores:
        return {
            "num_cases_with_multiple_reviewers": 0,
            "reviewer_pairs": [],
            "dimensions": {},
        }

    # Collect all reviewer IDs
    all_reviewers: set[str] = set()
    for scores_list in all_scores.values():
        for rs in scores_list:
            all_reviewers.add(rs.reviewer_id)

    reviewer_pairs = sorted(combinations(sorted(all_reviewers), 2))

    dimension_results: Dict[str, Dict[str, Any]] = {}
    for dim_name, (scale_str, _weight) in sorted(rubric_info.items()):
        parts = scale_str.split("-")
        scale_min = int(parts[0])
        scale_max = int(parts[1])

        pair_results: list[Dict[str, Any]] = []
        for r_a, r_b in reviewer_pairs:
            scores_a: list[int] = []
            scores_b: list[int] = []

            for case_id in sorted(all_scores.keys()):
                scores_list = all_scores[case_id]
                score_map: Dict[str, int | None] = {}
                for rs in scores_list:
                    dim_score = rs.dimensions.get(dim_name)
                    if dim_score is not None:
                        score_map[rs.reviewer_id] = dim_score.score

                if r_a in score_map and r_b in score_map:
                    sa = score_map[r_a]
                    sb = score_map[r_b]
                    if sa is not None and sb is not None:
                        scores_a.append(sa)
                        scores_b.append(sb)

            if not scores_a:
                continue

            pct = _compute_percent_agreement(scores_a, scores_b)
            kappa = _compute_cohens_kappa(scores_a, scores_b, scale_min, scale_max)

            pair_results.append(
                {
                    "reviewer_a": r_a,
                    "reviewer_b": r_b,
                    "num_cases": len(scores_a),
                    "percent_agreement": round(pct, 4),
                    "cohens_kappa": round(kappa, 4) if kappa is not None else None,
                    "interpretation": _interpret_kappa(kappa),
                }
            )

        dimension_results[dim_name] = {
            "scale": scale_str,
            "pairs": pair_results,
        }

    return {
        "num_cases_with_multiple_reviewers": len(all_scores),
        "reviewer_pairs": [list(p) for p in reviewer_pairs],
        "dimensions": dimension_results,
    }


def _write_calibration_json(path: Path, report: Mapping[str, Any]) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def _write_calibration_markdown(path: Path, report: Mapping[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Inter-Reviewer Calibration Report")
    lines.append("")

    num_cases = report.get("num_cases_with_multiple_reviewers", 0)
    lines.append(f"Cases with multiple reviewers: {num_cases}")
    lines.append("")

    if num_cases == 0:
        lines.append("No cases with multiple reviewers found. Nothing to report.")
        lines.append("")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    dimensions = report.get("dimensions", {})
    for dim_name, dim_data in sorted(dimensions.items()):
        if not isinstance(dim_data, Mapping):
            continue
        scale = dim_data.get("scale", "")
        lines.append(f"## {dim_name} (scale {scale})")
        lines.append("")
        lines.append(
            "| Reviewer A | Reviewer B | Cases | % Agreement | Cohen's Kappa | Interpretation |"
        )
        lines.append(
            "|------------|------------|-------|-------------|---------------|----------------|"
        )
        pairs = dim_data.get("pairs", [])
        for pair in pairs:
            r_a = pair.get("reviewer_a", "")
            r_b = pair.get("reviewer_b", "")
            n = pair.get("num_cases", 0)
            pct = pair.get("percent_agreement")
            pct_str = f"{pct:.1%}" if isinstance(pct, (int, float)) else "-"
            kappa = pair.get("cohens_kappa")
            kappa_str = f"{kappa:.4f}" if isinstance(kappa, (int, float)) else "-"
            interp = pair.get("interpretation", "")
            lines.append(f"| {r_a} | {r_b} | {n} | {pct_str} | {kappa_str} | {interp} |")
        lines.append("")

    lines.append("## Kappa interpretation guide")
    lines.append("")
    lines.append("| Kappa range | Interpretation |")
    lines.append("|-------------|----------------|")
    lines.append("| < 0.00 | Poor (less than chance) |")
    lines.append("| 0.00 - 0.20 | Slight |")
    lines.append("| 0.21 - 0.40 | Fair |")
    lines.append("| 0.41 - 0.60 | Moderate |")
    lines.append("| 0.61 - 0.80 | Substantial |")
    lines.append("| 0.81 - 1.00 | Almost perfect |")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = _get_repo_root()

    parser = argparse.ArgumentParser(
        prog="agenteval-eval-calibration",
        description=(
            "Compute pairwise inter-reviewer agreement (Cohen's Kappa) from reviewer score files."
        ),
    )
    parser.add_argument(
        "--scores-dir",
        type=str,
        default=str(repo_root / "scores"),
        help="Directory containing reviewer score files (default: scores/).",
    )
    parser.add_argument(
        "--rubric-path",
        type=str,
        default=str(repo_root / "rubrics" / "v1_agent_general.json"),
        help="Path to rubric config (JSON, default: rubrics/v1_agent_general.json).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=str(repo_root / "reports" / "calibration.json"),
        help="Path to write calibration JSON report (default: reports/calibration.json).",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=str(repo_root / "reports" / "calibration.md"),
        help="Path to write calibration Markdown report (default: reports/calibration.md).",
    )

    args = parser.parse_args(argv)

    scores_dir = _safe_resolve_within(repo_root, Path(args.scores_dir))
    rubric_path = _safe_resolve_within(repo_root, Path(args.rubric_path))
    output_json = _safe_resolve_within(repo_root, Path(args.output_json))
    output_md = _safe_resolve_within(repo_root, Path(args.output_md))

    rubric = load_rubric(rubric_path=rubric_path, schema_path=None)
    rubric_info: Dict[str, Tuple[str, float]] = {
        dim.name: (dim.scale, dim.weight) for dim in rubric.dimensions
    }

    case_ids = _collect_case_ids_from_scores_dir(scores_dir)

    report = compute_calibration_report(
        case_ids=case_ids,
        scores_dir=scores_dir,
        rubric_info=rubric_info,
    )

    output_json.parent.mkdir(parents=True, exist_ok=True)
    _write_calibration_json(output_json, report)
    _write_calibration_markdown(output_md, report)

    print(
        f"Wrote calibration reports to {output_json} and {output_md}.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
