from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple, cast

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within
from .loader import load_rubric, load_trace
from .tagger import tag_trace
from .types import CaseEvaluationTemplate, DimensionEvaluationTemplate, Rubric

from agenteval.schemas.trace import Trace as _Trace


@dataclass(frozen=True)
class _ExpectedOutcomeHeader:
    case_id: str | None
    primary_failure: str | None
    secondary_failures: Tuple[str, ...]
    severity: str | None
    case_version: str | None = None


def _parse_expected_outcome_header(path: Path) -> _ExpectedOutcomeHeader:
    """
    Parse the YAML-like header block at the top of expected_outcome.md.
    The format is:

    ---
    Case ID: XXX
    Primary Failure: <Failure Category>
    Secondary Failures: <Optional, comma-separated>
    Severity: <Low | Moderate | High | Critical>
    ---
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return _ExpectedOutcomeHeader(
            case_id=None,
            primary_failure=None,
            secondary_failures=tuple(),
            severity=None,
        )

    header: MutableMapping[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        header[key.strip().lower()] = value.strip()

    case_id = header.get("case id")
    primary = header.get("primary failure")
    secondary_raw = header.get("secondary failures")
    if secondary_raw:
        secondary = tuple(part.strip() for part in secondary_raw.split(",") if part.strip())
    else:
        secondary = tuple()
    severity = header.get("severity")
    case_version = header.get("case_version")

    return _ExpectedOutcomeHeader(
        case_id=case_id or None,
        primary_failure=primary or None,
        secondary_failures=secondary,
        severity=severity or None,
        case_version=case_version or None,
    )


def _summarize_trace(trace: Mapping[str, Any]) -> Dict[str, Any]:
    steps = trace.get("steps", [])
    if not isinstance(steps, list):
        steps = []

    type_counter: Counter[str] = Counter()
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        step_type = str(step.get("type", "unknown"))
        type_counter[step_type] += 1

    summary: Dict[str, Any] = {
        "num_steps": len(steps),
        "type_counts": dict(sorted(type_counter.items())),
    }

    metadata = trace.get("metadata")
    if isinstance(metadata, Mapping):
        timestamp = metadata.get("timestamp")
        if isinstance(timestamp, str):
            summary["run_timestamp"] = timestamp
        latency = metadata.get("latency_ms")
        if isinstance(latency, int):
            summary["run_latency_ms"] = latency

    return summary


def _build_case_template(
    case_id: str,
    trace: Mapping[str, Any],
    rubric: Rubric,
    header: _ExpectedOutcomeHeader,
) -> CaseEvaluationTemplate:
    task_id_raw = trace.get("task_id")
    task_id = str(task_id_raw) if isinstance(task_id_raw, str) else case_id

    trace_summary = _summarize_trace(trace)
    auto_tags = tag_trace(cast(_Trace, trace))

    dimensions: Dict[str, DimensionEvaluationTemplate] = {}
    for dim in rubric.dimensions:
        dimensions[dim.name] = DimensionEvaluationTemplate(
            dimension_name=dim.name,
            score=None,
            weight=dim.weight,
            scale=dim.scale,
            evidence_step_ids=tuple(),
            notes="",
        )

    labels: List[str] = []
    if header.primary_failure:
        labels.append(f"primary:{header.primary_failure}")
    labels.extend(f"secondary:{sec}" for sec in header.secondary_failures)
    if header.severity:
        labels.append(f"severity:{header.severity}")

    return CaseEvaluationTemplate(
        case_id=case_id,
        task_id=task_id,
        rubric_version=rubric.version,
        rubric_name=rubric.name,
        primary_failure=header.primary_failure,
        secondary_failures=header.secondary_failures,
        severity=header.severity,
        auto_tags=auto_tags,
        trace_summary=trace_summary,
        dimensions=dimensions,
        labels=labels,
        case_version=header.case_version,
    )


def _case_dirs(dataset_dir: Path) -> Iterable[Path]:
    for entry in sorted(dataset_dir.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            yield entry


def _write_json_template(path: Path, template: CaseEvaluationTemplate) -> None:
    data = asdict(template)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_markdown_template(path: Path, template: CaseEvaluationTemplate, rubric: Rubric) -> None:
    lines: List[str] = []
    lines.append(f"# Case {template.case_id} – Evaluation Template")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Case ID: `{template.case_id}`")
    lines.append(f"- Task ID: `{template.task_id}`")
    lines.append(f"- Rubric version: `{template.rubric_version}`")
    if template.rubric_name:
        lines.append(f"- Rubric name: {template.rubric_name}")
    if template.primary_failure:
        lines.append(f"- Primary failure: `{template.primary_failure}`")
    if template.secondary_failures:
        joined = ", ".join(f"`{sec}`" for sec in template.secondary_failures)
        lines.append(f"- Secondary failures: {joined}")
    if template.severity:
        lines.append(f"- Severity: `{template.severity}`")
    if template.auto_tags:
        tags = ", ".join(f"`{tag}`" for tag in template.auto_tags)
        lines.append(f"- Auto-detected tags: {tags}")
    if template.case_version:
        lines.append(f"- Case version: `{template.case_version}`")
    if template.labels:
        labels = ", ".join(template.labels)
        lines.append(f"- Labels: {labels}")

    lines.append("")
    lines.append("## Trace overview")
    lines.append("")
    summary = template.trace_summary
    lines.append(f"- Total steps/events: {summary.get('num_steps', 0)}")
    type_counts = summary.get("type_counts", {})
    if isinstance(type_counts, Mapping):
        lines.append("- Step types:")
        for step_type, count in sorted(type_counts.items()):
            lines.append(f"  - `{step_type}`: {count}")
    if "run_timestamp" in summary:
        lines.append(f"- Run timestamp: `{summary['run_timestamp']}`")
    if "run_latency_ms" in summary:
        lines.append(f"- Run latency (ms): {summary['run_latency_ms']}")

    lines.append("")
    lines.append("## Rubric dimensions (fill in scores)")
    lines.append("")
    lines.append("| Dimension | Scale | Weight | Description | Score | Evidence step_ids | Notes |")
    lines.append("|----------|-------|--------|-------------|-------|-------------------|-------|")

    for dim in rubric.dimensions:
        description = dim.description.replace("|", "\\|")
        lines.append(f"| `{dim.name}` | {dim.scale} | {dim.weight} | {description} |  |  |  |")

    lines.append("")
    lines.append("## Evaluation notes")
    lines.append("")
    lines.append(
        "Use this section to record overall reasoning, disagreements, or edge cases that "
        "are not captured by per-dimension scores."
    )
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = _get_repo_root()

    parser = argparse.ArgumentParser(
        prog="agenteval-eval-runner",
        description=(
            "Generate structured JSON + Markdown evaluation templates for AgentEval cases "
            "using a rubric."
        ),
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(repo_root / "data" / "cases"),
        help="Directory containing case folders (default: data/cases).",
    )
    parser.add_argument(
        "--rubric-path",
        type=str,
        default=str(repo_root / "rubrics" / "v1_agent_general.json"),
        help="Path to rubric config (JSON, default: rubrics/v1_agent_general.json).",
    )
    parser.add_argument(
        "--trace-schema-path",
        type=str,
        default=str(repo_root / "schemas" / "trace_schema.json"),
        help="Path to trace JSON Schema (default: schemas/trace_schema.json).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(repo_root / "reports"),
        help="Directory where evaluation templates will be written (default: reports/).",
    )

    args = parser.parse_args(argv)

    dataset_dir = _safe_resolve_within(repo_root, Path(args.dataset_dir))
    rubric_path = _safe_resolve_within(repo_root, Path(args.rubric_path))
    trace_schema_path = _safe_resolve_within(repo_root, Path(args.trace_schema_path))
    output_dir = _safe_resolve_within(repo_root, Path(args.output_dir))

    output_dir.mkdir(parents=True, exist_ok=True)

    rubric = load_rubric(rubric_path=rubric_path, schema_path=None)

    num_cases = 0
    for case_dir in _case_dirs(dataset_dir):
        case_id = case_dir.name
        trace_path = case_dir / "trace.json"
        outcome_path = case_dir / "expected_outcome.md"

        if not trace_path.exists() or not outcome_path.exists():
            continue

        trace = load_trace(trace_path=trace_path, schema_path=trace_schema_path)
        header = _parse_expected_outcome_header(outcome_path)
        template = _build_case_template(
            case_id=case_id,
            trace=trace,
            rubric=rubric,
            header=header,
        )

        json_out = output_dir / f"{case_id}.evaluation.json"
        md_out = output_dir / f"{case_id}.evaluation.md"
        _write_json_template(json_out, template)
        _write_markdown_template(md_out, template, rubric)
        num_cases += 1

    print(
        f"Generated evaluation templates for {num_cases} case(s) in {output_dir}.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
