"""Service layer for UI-facing orchestration.

Composes existing library APIs without modifying runner.py or report.py.
All Streamlit pages should import only from this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agenteval.dataset.generator import generate_case as _generator_generate_case
from agenteval.dataset.validator import (
    ValidationResult,
    _get_repo_root,
    validate_dataset as _validator_validate_dataset,
)
from agenteval.core.loader import load_trace as _loader_load_trace


def generate_case(
    case_id: str | None = None,
    failure_type: str | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Generate a benchmark case. Delegates to dataset.generator.generate_case()."""
    return _generator_generate_case(
        case_id=case_id,
        failure_type=failure_type,
        output_dir=output_dir,
        overwrite=overwrite,
    )


def validate_dataset(
    dataset_dir: Path | None = None,
    schema_path: Path | None = None,
) -> ValidationResult:
    """Validate the dataset. Delegates to dataset.validator.validate_dataset()."""
    return _validator_validate_dataset(
        dataset_dir=dataset_dir,
        schema_path=schema_path,
    )


def list_cases(dataset_dir: Path | None = None) -> list[str]:
    """List and sort case subdirectories in dataset_dir."""
    if dataset_dir is None:
        repo_root = _get_repo_root()
        dataset_dir = repo_root / "data" / "cases"
    if not dataset_dir.exists():
        return []
    return sorted(entry.name for entry in dataset_dir.iterdir() if entry.is_dir())


def load_case_metadata(case_dir: Path) -> dict[str, str | None]:
    """Read expected_outcome.md and parse YAML front matter header fields."""
    outcome_path = case_dir / "expected_outcome.md"
    if not outcome_path.exists():
        return {}

    text = outcome_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    header: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        header[key.strip().lower()] = value.strip()

    result: dict[str, str | None] = {
        "case_id": header.get("case id") or None,
        "primary_failure": header.get("primary failure") or None,
        "secondary_failures": header.get("secondary failures") or None,
        "severity": header.get("severity") or None,
        "case_version": header.get("case_version") or None,
    }
    return result


def load_trace(case_dir: Path) -> dict[str, Any]:
    """Load and validate trace.json from a case directory."""
    trace_path = case_dir / "trace.json"
    return _loader_load_trace(trace_path=trace_path)


def load_evaluation_template(
    case_id: str,
    reports_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Read a case evaluation template JSON, or return None if it doesn't exist."""
    if reports_dir is None:
        repo_root = _get_repo_root()
        reports_dir = repo_root / "reports"
    path = reports_dir / f"{case_id}.evaluation.json"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    result: dict[str, Any] = json.loads(text)
    return result


def run_evaluation(
    dataset_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Run the evaluation pipeline by calling runner.main() with constructed argv.

    Returns list of evaluation template dicts (one per case).
    Raises RuntimeError if runner returns non-zero.
    """
    from agenteval.core.runner import main as runner_main

    repo_root = _get_repo_root()
    if dataset_dir is None:
        dataset_dir = repo_root / "data" / "cases"
    if output_dir is None:
        output_dir = repo_root / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)

    argv = [
        "--dataset-dir",
        str(dataset_dir),
        "--output-dir",
        str(output_dir),
    ]

    exit_code = runner_main(argv)
    if exit_code != 0:
        msg = f"Evaluation runner failed with exit code {exit_code}"
        raise RuntimeError(msg)

    # Read all generated evaluation JSON files
    results: list[dict[str, Any]] = []
    for path in sorted(output_dir.iterdir(), key=lambda p: p.name):
        if (
            path.is_file()
            and path.name.endswith(".evaluation.json")
            and not path.name.startswith("summary")
        ):
            text = path.read_text(encoding="utf-8")
            results.append(json.loads(text))
    return results


def generate_summary_report(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate aggregated summary report by calling report.main() with constructed argv.

    Returns the summary report dict.
    Raises RuntimeError if report returns non-zero or raises SystemExit.
    """
    from agenteval.core.report import main as report_main

    repo_root = _get_repo_root()
    if input_dir is None:
        input_dir = repo_root / "reports"
    if output_dir is None:
        output_dir = repo_root / "reports"

    output_json = output_dir / "summary.evaluation.json"
    output_md = output_dir / "summary.evaluation.md"

    argv = [
        "--input-dir",
        str(input_dir),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ]

    try:
        exit_code = report_main(argv)
    except SystemExit as exc:
        msg = f"Report generation failed: {exc}"
        raise RuntimeError(msg) from exc

    if exit_code != 0:
        msg = f"Report generation failed with exit code {exit_code}"
        raise RuntimeError(msg)

    if not output_json.exists():
        msg = f"Expected summary file not found: {output_json}"
        raise RuntimeError(msg)

    text = output_json.read_text(encoding="utf-8")
    result: dict[str, Any] = json.loads(text)
    return result
