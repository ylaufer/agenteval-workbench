"""Run tracking for the evaluation pipeline.

Each evaluation execution produces a tracked run with a unique ID,
timestamps, dataset path reference, and configuration. Run results
are persisted exclusively under runs/<run_id>/.
"""

from __future__ import annotations

import argparse
import json
import secrets
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
    """Load all per-case evaluation templates from a run.

    Returns list of evaluation template dicts sorted by case_id.
    Returns empty list if run directory doesn't exist.
    """
    run_dir = get_run_dir(run_id)
    if not run_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for path in sorted(run_dir.iterdir(), key=lambda p: p.name):
        if (
            path.is_file()
            and path.name.endswith(".evaluation.json")
            and not path.name.startswith("summary")
        ):
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            results.append(data)
    return results


def get_run_summary(run_id: str) -> dict[str, Any] | None:
    """Load the summary report from a run. Returns None if not found."""
    summary_path = get_run_dir(run_id) / "summary.evaluation.json"
    if not summary_path.exists():
        return None
    data: dict[str, Any] = json.loads(summary_path.read_text(encoding="utf-8"))
    return data


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
        print("No evaluation runs found. Run an evaluation first:")
        print("  agenteval-eval-runner --dataset-dir data/cases --output-dir runs/<run_id>")
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
