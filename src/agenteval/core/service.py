"""Service layer for UI-facing orchestration.

Composes existing library APIs without modifying runner.py or report.py.
All Streamlit pages should import only from this module.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agenteval.dataset.generator import generate_case as _generator_generate_case
from agenteval.dataset.validator import (
    ValidationResult,
    _get_repo_root,
    _safe_resolve_within,
    validate_dataset as _validator_validate_dataset,
)
from agenteval.core.loader import load_trace as _loader_load_trace
from agenteval.ingestion import auto_detect_adapter, get_adapter_by_name


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


def get_next_case_id(dataset_dir: Path | None = None) -> str:
    """Return the next available case ID by scanning existing cases.

    Scans data/cases/ directory, extracts numeric suffixes from case_NNN pattern,
    finds the maximum N, and returns case_{max_n + 1:03d}.

    Returns "case_001" if no cases exist.
    """
    if dataset_dir is None:
        repo_root = _get_repo_root()
        dataset_dir = repo_root / "data" / "cases"

    if not dataset_dir.exists():
        return "case_001"

    max_n = 0
    for entry in dataset_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("case_"):
            try:
                n = int(entry.name.split("_")[1])
                max_n = max(max_n, n)
            except (IndexError, ValueError):
                continue

    return f"case_{max_n + 1:03d}"


def ingest_trace(
    raw_content: dict[str, Any],
    adapter_name: str = "auto",
    mapping_config: dict[str, Any] | None = None,
    output_case_id: str | None = None,
    original_filename: str = "trace.json",
) -> dict[str, Any]:
    """Convert a single trace file using specified adapter and create complete case directory.

    Args:
        raw_content: Parsed JSON content from uploaded file
        adapter_name: Adapter to use ("auto", "otel", "langchain", "crewai", "openai", "generic")
        mapping_config: Mapping config dict for Generic adapter (required if adapter_name == "generic")
        output_case_id: Target case ID (e.g., "case_042"). If None, calls get_next_case_id()
        original_filename: Original uploaded filename (for placeholder metadata)

    Returns:
        dict with keys: case_id, trace_path, adapter_name, step_count, step_types, warnings, validation_errors

    Raises:
        ValueError: Format not recognized (auto-detect failed), schema validation failed,
                   or Generic adapter selected but no mapping config provided
        FileExistsError: Case directory already exists
    """
    import jsonschema

    repo_root = _get_repo_root()

    # Step 1: Determine adapter
    if adapter_name == "auto":
        adapter = auto_detect_adapter(raw_content)
        if adapter is None:
            msg = "Format not recognized. Try selecting an adapter manually."
            raise ValueError(msg)
        adapter_display_name = f"Auto-detected: {adapter.__class__.__name__}"
    else:
        adapter = get_adapter_by_name(adapter_name)
        if adapter is None:
            msg = f"Unknown adapter: {adapter_name}"
            raise ValueError(msg)
        adapter_display_name = adapter.__class__.__name__

        # Check Generic adapter has mapping config
        if adapter_name == "generic" and mapping_config is None:
            msg = "Generic adapter requires a mapping config"
            raise ValueError(msg)

    # Step 2: Convert trace
    if adapter_name == "generic" and mapping_config is not None:
        # Generic adapter needs mapping config passed during conversion
        # Check if adapter has a method to set mapping config
        if hasattr(adapter, "set_mapping"):
            adapter.set_mapping(mapping_config)
        converted_trace = adapter.convert(raw_content)
    else:
        converted_trace = adapter.convert(raw_content)

    # Step 3: Validate trace against schema
    schema_path = repo_root / "schemas" / "trace_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validation_errors: list[str] = []
    try:
        jsonschema.validate(instance=converted_trace, schema=schema)
    except jsonschema.ValidationError as exc:
        validation_errors.append(str(exc.message))
        msg = f"Schema validation failed: {exc.message}"
        raise ValueError(msg) from exc

    # Step 4: Determine case directory
    if output_case_id is None:
        output_case_id = get_next_case_id()

    case_dir = repo_root / "data" / "cases" / output_case_id
    # Verify path is within repo root
    _safe_resolve_within(repo_root, case_dir)

    if case_dir.exists():
        msg = f"Case directory already exists: {case_dir}"
        raise FileExistsError(msg)

    # Step 5: Create case directory
    case_dir.mkdir(parents=True, exist_ok=False)

    # Step 6: Write trace.json
    trace_path = case_dir / "trace.json"
    trace_path.write_text(json.dumps(converted_trace, indent=2), encoding="utf-8")

    # Step 7: Write prompt.txt placeholder
    timestamp = datetime.now().isoformat()
    prompt_content = f"""[TODO: Add the agent prompt that produced this trace]

This trace was ingested from: {original_filename}
Adapter used: {adapter_display_name}
Ingested on: {timestamp}
"""
    prompt_path = case_dir / "prompt.txt"
    prompt_path.write_text(prompt_content, encoding="utf-8")

    # Step 8: Write expected_outcome.md placeholder
    outcome_content = """---
primary_failure: unknown
severity: unknown
tags: []
notes: ""
---

# Expected Outcome

[TODO: Describe the expected behavior and actual failure observed in this trace]

## Primary Failure Type

[TODO: Select one of the 12 canonical failure types from docs/failure_taxonomy.md]

## Evaluation Guidance

[TODO: Provide guidance for human reviewers on what to look for when evaluating this case]
"""
    outcome_path = case_dir / "expected_outcome.md"
    outcome_path.write_text(outcome_content, encoding="utf-8")

    # Step 9: Calculate step statistics
    steps = converted_trace.get("steps", [])
    step_count = len(steps)
    step_types: dict[str, int] = {}
    for step in steps:
        step_type = step.get("type", "unknown")
        step_types[step_type] = step_types.get(step_type, 0) + 1

    # Step 10: Collect warnings (adapter-specific)
    warnings: list[str] = []
    if hasattr(adapter, "get_warnings"):
        warnings = adapter.get_warnings()

    return {
        "case_id": output_case_id,
        "trace_path": str(trace_path),
        "adapter_name": adapter_display_name,
        "step_count": step_count,
        "step_types": step_types,
        "warnings": warnings,
        "validation_errors": validation_errors,
    }


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
    """Run the evaluation pipeline with automatic run tracking.

    Creates a tracked run, directs output to the run directory, generates
    the summary report, and marks the run as completed or failed.

    Returns list of evaluation template dicts (one per case).
    Raises RuntimeError if runner returns non-zero.
    """
    from agenteval.core.report import main as report_main
    from agenteval.core.runner import main as runner_main
    from agenteval.core.runs import (
        complete_run,
        create_run,
        fail_run,
        get_run_dir,
        get_run_results as _get_run_results,
    )

    repo_root = _get_repo_root()
    if dataset_dir is None:
        dataset_dir = repo_root / "data" / "cases"

    rubric_path = repo_root / "rubrics" / "v1_agent_general.json"

    # Create tracked run
    record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
    run_dir = get_run_dir(record.run_id)

    # If caller specified output_dir, use it; otherwise use the run directory
    effective_output = output_dir if output_dir is not None else run_dir

    argv = [
        "--dataset-dir",
        str(dataset_dir),
        "--output-dir",
        str(effective_output),
    ]

    try:
        exit_code = runner_main(argv)
        if exit_code != 0:
            fail_run(record.run_id, f"Runner exited with code {exit_code}")
            msg = f"Evaluation runner failed with exit code {exit_code}"
            raise RuntimeError(msg)
    except RuntimeError:
        raise
    except Exception as exc:
        fail_run(record.run_id, str(exc))
        raise

    # Count evaluation files produced
    results = _get_run_results(record.run_id) if output_dir is None else []
    if output_dir is None:
        num_cases = len(results)
    else:
        num_cases = sum(
            1
            for p in effective_output.iterdir()
            if p.is_file()
            and p.name.endswith(".evaluation.json")
            and not p.name.startswith("summary")
        )

    # Generate summary report in the run directory
    if output_dir is None:
        try:
            summary_json = effective_output / "summary.evaluation.json"
            summary_md = effective_output / "summary.evaluation.md"
            report_argv = [
                "--input-dir",
                str(effective_output),
                "--output-json",
                str(summary_json),
                "--output-md",
                str(summary_md),
            ]
            report_main(report_argv)
        except (SystemExit, Exception):
            pass  # Summary generation is best-effort; don't fail the run

    complete_run(record.run_id, num_cases=num_cases)

    # Read results from effective output
    if not results:
        for path in sorted(effective_output.iterdir(), key=lambda p: p.name):
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


# ---------------------------------------------------------------------------
# Run management
# ---------------------------------------------------------------------------


def list_runs() -> list[dict[str, Any]]:
    """List all runs in reverse chronological order. Returns list of dicts."""
    from agenteval.core.runs import list_runs as _list_runs
    from dataclasses import asdict

    return [asdict(r) for r in _list_runs()]


def get_run(run_id: str) -> dict[str, Any] | None:
    """Retrieve a specific run by ID. Returns dict or None."""
    from agenteval.core.runs import get_run as _get_run
    from dataclasses import asdict

    record = _get_run(run_id)
    if record is None:
        return None
    return asdict(record)


def get_run_results(run_id: str) -> list[dict[str, Any]]:
    """Load all per-case evaluation templates from a run."""
    from agenteval.core.runs import get_run_results as _get_run_results

    return _get_run_results(run_id)


def get_run_summary(run_id: str) -> dict[str, Any] | None:
    """Load the summary report from a run."""
    from agenteval.core.runs import get_run_summary as _get_run_summary

    return _get_run_summary(run_id)


# ---------------------------------------------------------------------------
# Auto-scoring
# ---------------------------------------------------------------------------


def run_auto_scoring(
    dataset_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Run auto-scoring pipeline with run tracking.

    Creates a tracked run, scores all cases using rule-based (and optionally
    LLM-based) evaluators, writes auto_evaluation.json files, and marks the
    run as completed or failed.

    Returns list of auto-evaluation dicts.
    """
    from agenteval.core.runs import (
        complete_run,
        create_run,
        fail_run,
        get_run_dir,
    )
    from agenteval.core.scorer import score_dataset

    repo_root = _get_repo_root()
    if dataset_dir is None:
        dataset_dir = repo_root / "data" / "cases"

    rubric_path = repo_root / "rubrics" / "v1_agent_general.json"

    # Create tracked run
    record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
    run_dir = get_run_dir(record.run_id)

    effective_output = output_dir if output_dir is not None else run_dir

    try:
        results = score_dataset(
            dataset_dir=dataset_dir,
            output_dir=effective_output,
            rubric_path=rubric_path,
        )
    except Exception as exc:
        fail_run(record.run_id, str(exc))
        raise

    complete_run(record.run_id, num_cases=len(results))
    return results
