"""Run tracking for the evaluation pipeline.

Each evaluation execution produces a tracked run with a unique ID,
timestamps, dataset path reference, and configuration. Run results
are persisted exclusively under runs/<run_id>/.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within
from agenteval.core.types import RunRecord, RunStatus


def generate_run_id() -> str:
    """Generate a unique run identifier in YYYYMMDDTHHMMSS_xxxx format."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = secrets.token_hex(2)
    return f"{ts}_{suffix}"


def _runs_dir() -> Path:
    """Return the runs/ directory under the repo root."""
    repo_root = _get_repo_root()
    return repo_root / "runs"


def get_run_dir(run_id: str) -> Path:
    """Get the filesystem path for a run's directory."""
    return _runs_dir() / run_id


def _read_run_json(run_id: str) -> RunRecord | None:
    """Read run.json and return a RunRecord, or None if not found."""
    run_json = get_run_dir(run_id) / "run.json"
    if not run_json.exists():
        return None
    data = json.loads(run_json.read_text(encoding="utf-8"))
    return RunRecord(**data)


def _write_run_json(record: RunRecord) -> None:
    """Write a RunRecord to runs/<run_id>/run.json."""
    run_dir = get_run_dir(record.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    run_json = run_dir / "run.json"
    run_json.write_text(
        json.dumps(asdict(record), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def create_run(dataset_dir: Path, rubric_path: Path) -> RunRecord:
    """Create a new run record and its directory.

    Validates paths via _safe_resolve_within(). Returns RunRecord with
    status 'running'. Raises ValueError if paths are outside repo root.
    """
    repo_root = _get_repo_root()
    resolved_dataset = _safe_resolve_within(repo_root, dataset_dir)
    resolved_rubric = _safe_resolve_within(repo_root, rubric_path)

    run_id = generate_run_id()
    now = datetime.now(timezone.utc).isoformat()

    record = RunRecord(
        run_id=run_id,
        status=RunStatus.RUNNING.value,
        started_at=now,
        dataset_dir=str(resolved_dataset),
        rubric_path=str(resolved_rubric),
        num_cases=0,
    )
    _write_run_json(record)
    return record


def complete_run(run_id: str, num_cases: int) -> RunRecord:
    """Mark a run as completed.

    Raises FileNotFoundError if run doesn't exist.
    """
    existing = _read_run_json(run_id)
    if existing is None:
        msg = f"Run '{run_id}' not found"
        raise FileNotFoundError(msg)

    now = datetime.now(timezone.utc).isoformat()
    updated = RunRecord(
        run_id=existing.run_id,
        status=RunStatus.COMPLETED.value,
        started_at=existing.started_at,
        dataset_dir=existing.dataset_dir,
        rubric_path=existing.rubric_path,
        num_cases=num_cases,
        completed_at=now,
        error=None,
        filter_criteria=existing.filter_criteria,
    )
    _write_run_json(updated)
    return updated


def fail_run(run_id: str, error: str, num_cases: int = 0) -> RunRecord:
    """Mark a run as failed.

    Raises FileNotFoundError if run doesn't exist.
    """
    existing = _read_run_json(run_id)
    if existing is None:
        msg = f"Run '{run_id}' not found"
        raise FileNotFoundError(msg)

    updated = RunRecord(
        run_id=existing.run_id,
        status=RunStatus.FAILED.value,
        started_at=existing.started_at,
        dataset_dir=existing.dataset_dir,
        rubric_path=existing.rubric_path,
        num_cases=num_cases,
        completed_at=None,
        error=error,
        filter_criteria=existing.filter_criteria,
    )
    _write_run_json(updated)
    return updated


def get_run(run_id: str) -> RunRecord | None:
    """Retrieve a specific run by ID. Returns None if not found."""
    return _read_run_json(run_id)


def list_runs() -> list[RunRecord]:
    """List all runs in reverse chronological order.

    Scans runs/ directory, reads run.json from each subdirectory.
    Skips directories with missing or invalid run.json.
    Returns empty list if runs/ directory doesn't exist.
    """
    runs_root = _runs_dir()
    if not runs_root.exists():
        return []

    records: list[RunRecord] = []
    for entry in runs_root.iterdir():
        if not entry.is_dir():
            continue
        run_json = entry / "run.json"
        if not run_json.exists():
            continue
        try:
            data = json.loads(run_json.read_text(encoding="utf-8"))
            records.append(RunRecord(**data))
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    records.sort(key=lambda r: r.started_at, reverse=True)
    return records


def get_run_results(run_id: str) -> list[dict[str, Any]]:
    """Load all per-case evaluation results from a run.

    Prefers *.auto_evaluation.json (from auto-scoring) over *.evaluation.json
    (runner templates) when both exist for the same case. Returns list sorted
    by case_id. Returns empty list if run directory doesn't exist.
    """
    run_dir = get_run_dir(run_id)
    if not run_dir.exists():
        return []

    # Collect both file types; auto_evaluation takes precedence per case_id
    by_case: dict[str, Path] = {}
    for path in run_dir.iterdir():
        if not path.is_file() or path.name.startswith("summary"):
            continue
        if path.name.endswith(".auto_evaluation.json"):
            case_id = path.name[: -len(".auto_evaluation.json")]
            by_case[case_id] = path  # always wins
        elif path.name.endswith(".evaluation.json") and path.name not in by_case:
            case_id = path.name[: -len(".evaluation.json")]
            if case_id not in by_case:
                by_case[case_id] = path

    results: list[dict[str, Any]] = []
    for case_id in sorted(by_case):
        data: dict[str, Any] = json.loads(by_case[case_id].read_text(encoding="utf-8"))
        results.append(data)
    return results


def get_run_summary(run_id: str) -> dict[str, Any] | None:
    """Load the summary report from a run. Returns None if not found."""
    summary_path = get_run_dir(run_id) / "summary.evaluation.json"
    if not summary_path.exists():
        return None
    data: dict[str, Any] = json.loads(summary_path.read_text(encoding="utf-8"))
    return data


def _set_filter_criteria(run_id: str, criteria: dict[str, Any]) -> None:
    """Persist filter_criteria into an existing run.json."""
    run_json = get_run_dir(run_id) / "run.json"
    if not run_json.exists():
        return
    data = json.loads(run_json.read_text(encoding="utf-8"))
    data["filter_criteria"] = criteria
    run_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------


def main_list(argv: Sequence[str] | None = None) -> int:
    """CLI: list all evaluation runs."""
    parser = argparse.ArgumentParser(
        prog="agenteval-list-runs",
        description="List all evaluation runs in reverse chronological order.",
    )
    parser.parse_args(argv)

    runs = list_runs()
    if not runs:
        print("No evaluation runs found. Create one with:")
        print("  agenteval-run --dataset-dir data/cases")
        return 0

    header = f"{'Run ID':<26}  {'Status':<10}  {'Cases':>5}  {'Started'}"
    sep = f"{'─' * 26}  {'─' * 10}  {'─' * 5}  {'─' * 19}"
    print(header)
    print(sep)
    for run in runs:
        # Parse ISO timestamp to readable format
        started = run.started_at[:19].replace("T", " ")
        print(f"{run.run_id:<26}  {run.status:<10}  {run.num_cases:>5}  {started}")

    return 0


def main_inspect(argv: Sequence[str] | None = None) -> int:
    """CLI: inspect a specific evaluation run."""
    parser = argparse.ArgumentParser(
        prog="agenteval-inspect-run",
        description="Inspect a specific evaluation run by its identifier.",
    )
    parser.add_argument("run_id", type=str, help="The run identifier to inspect.")
    args = parser.parse_args(argv)

    run = get_run(args.run_id)
    if run is None:
        print(f"Error: Run '{args.run_id}' not found.")
        return 1

    print(f"Run: {run.run_id}")
    print(f"Status: {run.status}")
    started = run.started_at[:19].replace("T", " ")
    print(f"Started: {started} UTC")
    if run.completed_at:
        completed = run.completed_at[:19].replace("T", " ")
        print(f"Completed: {completed} UTC")
    print(f"Dataset: {run.dataset_dir}")
    print(f"Rubric: {run.rubric_path}")
    print(f"Cases evaluated: {run.num_cases}")

    if run.error:
        print(f"Error: {run.error}")

    # Show per-case results if available
    results = get_run_results(run.run_id)
    if results:
        print()
        print("Per-case results:")
        header = f"  {'Case ID':<20}  {'Primary Failure':<28}  {'Severity'}"
        print(header)
        sep = f"  {'─' * 20}  {'─' * 28}  {'─' * 8}"
        print(sep)
        for result in results:
            case_id = result.get("case_id", "?")
            primary = result.get("primary_failure") or "—"
            severity = result.get("severity") or "—"
            print(f"  {case_id:<20}  {primary:<28}  {severity}")

    return 0


def main_run(argv: Sequence[str] | None = None) -> int:
    """CLI: agenteval-run — create a tracked evaluation run end-to-end.

    Combines create_run + score_dataset + complete_run into one command.
    Prints the run ID on success so it can be passed to agenteval-compare.
    """
    parser = argparse.ArgumentParser(
        prog="agenteval-run",
        description=(
            "Create a tracked evaluation run: score all matching cases and mark "
            "the run complete. Prints the run ID on success for use with "
            "agenteval-compare."
        ),
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to dataset directory (default: data/cases)",
    )
    parser.add_argument(
        "--rubric",
        type=str,
        default=None,
        help="Path to rubric JSON file (default: rubrics/v1_agent_general.json)",
    )
    parser.add_argument(
        "--cases",
        type=str,
        default=None,
        help="Comma-separated case IDs to score (e.g., case_001,case_003).",
    )
    parser.add_argument(
        "--filter-failure",
        type=str,
        default=None,
        help="Filter cases by primary_failure value (case-insensitive).",
    )
    parser.add_argument(
        "--filter-severity",
        type=str,
        default=None,
        help="Comma-separated severity levels to include (e.g., Critical,High).",
    )
    parser.add_argument(
        "--filter-tag",
        type=str,
        default=None,
        help="Comma-separated tags; case must have ALL listed tags.",
    )
    parser.add_argument(
        "--filter-pattern",
        type=str,
        default=None,
        help="Glob pattern matched against case directory name (e.g., case_0*).",
    )

    args = parser.parse_args(argv)
    repo_root = _get_repo_root()

    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else repo_root / "data" / "cases"
    rubric_path = (
        Path(args.rubric) if args.rubric else repo_root / "rubrics" / "v1_agent_general.json"
    )

    dataset_dir = _safe_resolve_within(repo_root, dataset_dir)
    rubric_path = _safe_resolve_within(repo_root, rubric_path)

    if not dataset_dir.exists():
        print(f"Error: Dataset directory not found: {dataset_dir}", file=sys.stderr)
        return 2

    # Create tracked run — this generates the run_id and runs/ directory
    record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
    run_id = record.run_id
    output_dir = get_run_dir(run_id)

    print(f"Started run: {run_id}")

    # Deferred imports to avoid circular dependencies at module load time
    from agenteval.core.filtering import filter_cases
    from agenteval.core.scorer import default_registry, score_dataset

    all_case_dirs = sorted(
        (entry for entry in dataset_dir.iterdir() if entry.is_dir()),
        key=lambda p: p.name,
    )

    case_ids: list[str] | None = None
    if args.cases:
        requested = [c.strip() for c in args.cases.split(",") if c.strip()]
        known = {d.name for d in all_case_dirs}
        valid: list[str] = []
        for cid in requested:
            if cid in known:
                valid.append(cid)
            else:
                print(
                    f"Warning: case '{cid}' not found in {dataset_dir}, skipping.",
                    file=sys.stderr,
                )
        case_ids = valid

    severity_list: list[str] | None = (
        [s.strip() for s in args.filter_severity.split(",") if s.strip()]
        if args.filter_severity
        else None
    )
    tag_list: list[str] | None = (
        [t.strip() for t in args.filter_tag.split(",") if t.strip()]
        if args.filter_tag
        else None
    )

    any_filter = (
        case_ids is not None
        or args.filter_failure is not None
        or severity_list is not None
        or tag_list is not None
        or args.filter_pattern is not None
    )

    case_filter: list[Path] | None = None
    if any_filter:
        case_filter = filter_cases(
            case_dirs=all_case_dirs,
            case_ids=case_ids,
            failure_type=args.filter_failure,
            severity=severity_list,
            tags=tag_list,
            pattern=args.filter_pattern,
        )
        if not case_filter:
            fail_run(run_id, "No cases matched the specified filter.")
            print("No cases matched the specified filter.")
            return 0

        criteria: dict[str, Any] = {}
        if case_ids is not None:
            criteria["cases"] = case_ids
        if args.filter_failure:
            criteria["failure_type"] = args.filter_failure
        if severity_list:
            criteria["severity"] = severity_list
        if tag_list:
            criteria["tags"] = tag_list
        if args.filter_pattern:
            criteria["pattern"] = args.filter_pattern
        _set_filter_criteria(run_id, criteria)

    try:
        results = score_dataset(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            rubric_path=rubric_path,
            registry=default_registry(),
            case_filter=case_filter,
        )
    except Exception as exc:
        fail_run(run_id, str(exc))
        print(f"Error during scoring: {exc}", file=sys.stderr)
        return 1

    complete_run(run_id, num_cases=len(results))

    if not results:
        print("No cases found to score.")
        print(f"Run ID: {run_id} (0 cases, marked complete)")
        return 0

    print(f"\nScored {len(results)} case(s):")
    for r in results:
        dims = r.get("dimensions", {})
        scored_names = [
            f"{name}={d['score']}"
            for name, d in dims.items()
            if isinstance(d, dict) and d.get("score") is not None
        ]
        detail = ", ".join(scored_names) if scored_names else "none"
        print(f"  {r['case_id']}: {detail}")

    print(f"\nRun complete. Run ID: {run_id}")
    print(f"Compare runs:  agenteval-compare --baseline <other-run> --current {run_id}")
    return 0
