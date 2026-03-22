from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within

# The 12 canonical failure categories from the failure taxonomy.
VALID_FAILURE_TYPES = (
    "tool_hallucination",
    "unnecessary_tool_invocation",
    "instruction_drift",
    "partial_completion",
    "tool_schema_misuse",
    "ui_grounding_mismatch",
    "unsafe_output",
    "format_violation",
    "latency_mismanagement",
    "reasoning_inconsistency",
    "constraint_violation",
    "incomplete_execution",
)

# Human-readable display names for each failure type.
_FAILURE_DISPLAY_NAMES: dict[str, str] = {
    "tool_hallucination": "Tool Hallucination",
    "unnecessary_tool_invocation": "Unnecessary Tool Invocation",
    "instruction_drift": "Instruction Drift",
    "partial_completion": "Partial Completion",
    "tool_schema_misuse": "Tool Schema Misuse",
    "ui_grounding_mismatch": "UI Grounding Mismatch",
    "unsafe_output": "Unsafe Output",
    "format_violation": "Format Violation",
    "latency_mismanagement": "Latency Mismanagement",
    "reasoning_inconsistency": "Reasoning Inconsistency",
    "constraint_violation": "Constraint Violation",
    "incomplete_execution": "Incomplete Execution",
}

_FAILURE_SEVERITY: dict[str, str] = {
    "tool_hallucination": "Critical",
    "unnecessary_tool_invocation": "Moderate",
    "instruction_drift": "High",
    "partial_completion": "High",
    "tool_schema_misuse": "High",
    "ui_grounding_mismatch": "Moderate",
    "unsafe_output": "Critical",
    "format_violation": "Moderate",
    "latency_mismanagement": "Low",
    "reasoning_inconsistency": "High",
    "constraint_violation": "High",
    "incomplete_execution": "High",
}


def _build_trace(case_id: str, failure_type: str | None) -> dict[str, Any]:
    """Build a schema-valid trace dict, optionally reflecting a failure pattern."""
    started_at = int(time.time() * 1000)

    steps: list[dict[str, Any]]

    if failure_type == "tool_hallucination":
        prompt = "Look up the weather in Paris and summarize."
        steps = [
            {
                "step_id": "s1",
                "type": "thought",
                "actor_id": "agent",
                "content": "I will search for Paris weather.",
            },
            {
                "step_id": "s2",
                "type": "final_answer",
                "actor_id": "agent",
                "content": "The weather tool returned sunny and 25C in Paris.",
            },
        ]
    elif failure_type == "unnecessary_tool_invocation":
        prompt = "What is 2 + 2?"
        steps = [
            {
                "step_id": "s1",
                "type": "tool_call",
                "actor_id": "agent",
                "content": "Calling calculator for 2+2",
                "tool_name": "calculator",
                "tool_input": {"expression": "2+2"},
            },
            {
                "step_id": "s2",
                "type": "observation",
                "actor_id": "tool",
                "content": "4",
                "tool_output": "4",
            },
            {
                "step_id": "s3",
                "type": "final_answer",
                "actor_id": "agent",
                "content": "2 + 2 = 4",
            },
        ]
    else:
        prompt = "Demonstrate a generic agent interaction."
        steps = [
            {
                "step_id": "s1",
                "type": "thought",
                "actor_id": "agent",
                "content": "Thinking about the task.",
            },
            {
                "step_id": "s2",
                "type": "tool_call",
                "actor_id": "agent",
                "content": "Calling search tool",
                "tool_name": "search",
                "tool_input": {"query": "test"},
            },
            {
                "step_id": "s3",
                "type": "observation",
                "actor_id": "tool",
                "content": "Search returned results.",
                "tool_output": "result data",
            },
            {
                "step_id": "s4",
                "type": "final_answer",
                "actor_id": "agent",
                "content": "Here is the answer.",
            },
        ]

    finished_at = int(time.time() * 1000)

    return {
        "run_id": str(uuid.uuid4()),
        "task_id": case_id,
        "user_prompt": prompt,
        "model_version": "generated-v1",
        "steps": steps,
        "metadata": {
            "timestamp": str(started_at),
            "latency_ms": finished_at - started_at,
        },
    }


def _build_prompt(failure_type: str | None) -> str:
    """Build prompt.txt content for the case."""
    if failure_type and failure_type in _FAILURE_DISPLAY_NAMES:
        return f"Demonstrate a {_FAILURE_DISPLAY_NAMES[failure_type]} failure scenario.\n"
    return "Demonstrate a generic agent interaction.\n"


def _build_expected_outcome(case_id: str, failure_type: str | None) -> str:
    """Build expected_outcome.md with all 5 required header fields."""
    if failure_type and failure_type in _FAILURE_DISPLAY_NAMES:
        primary = _FAILURE_DISPLAY_NAMES[failure_type]
        severity = _FAILURE_SEVERITY.get(failure_type, "Moderate")
    else:
        primary = "None"
        severity = "Low"

    return (
        "---\n"
        f"Case ID: {case_id}\n"
        f"Primary Failure: {primary}\n"
        "Secondary Failures:\n"
        f"Severity: {severity}\n"
        "case_version: 1.0\n"
        "---\n\n"
        f"Generated case for {primary.lower() if primary != 'None' else 'generic'} scenario.\n"
    )


def generate_case(
    case_id: str | None = None,
    failure_type: str | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Generate a complete, schema-valid case directory.

    Returns the path to the created case directory.
    Raises ValueError if case exists and overwrite is False.
    Raises ValueError if failure_type is not a valid taxonomy entry.
    Raises ValueError if output_dir is outside the repo root.
    """
    repo_root = _get_repo_root()

    if failure_type is not None and failure_type not in VALID_FAILURE_TYPES:
        raise ValueError(
            f"Invalid failure_type: {failure_type!r}. Valid types: {', '.join(VALID_FAILURE_TYPES)}"
        )

    if case_id is None:
        case_id = f"generated_{uuid.uuid4().hex[:8]}"

    if output_dir is None:
        output_dir = repo_root / "data" / "cases"

    # Validate output_dir is within repo root
    output_dir = _safe_resolve_within(repo_root, output_dir)

    case_dir = output_dir / case_id

    if case_dir.exists() and not overwrite:
        raise ValueError(
            f"Case directory already exists: {case_dir}. Use overwrite=True to replace."
        )

    case_dir.mkdir(parents=True, exist_ok=True)

    # Write prompt.txt
    (case_dir / "prompt.txt").write_text(_build_prompt(failure_type), encoding="utf-8")

    # Write trace.json
    trace = _build_trace(case_id, failure_type)
    (case_dir / "trace.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Write expected_outcome.md
    (case_dir / "expected_outcome.md").write_text(
        _build_expected_outcome(case_id, failure_type),
        encoding="utf-8",
    )

    return case_dir


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for agenteval-generate-case."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="agenteval-generate-case",
        description="Generate a complete, schema-valid AgentEval benchmark case.",
    )
    parser.add_argument(
        "--case-id",
        default=None,
        help="Case directory name (default: auto-generated).",
    )
    parser.add_argument(
        "--failure-type",
        default=None,
        choices=VALID_FAILURE_TYPES,
        help="Failure category from the taxonomy.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Parent directory for the case (default: data/cases).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing case directory.",
    )

    args = parser.parse_args(argv)

    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        case_dir = generate_case(
            case_id=args.case_id,
            failure_type=args.failure_type,
            output_dir=output_dir,
            overwrite=args.overwrite,
        )
        print(f"Generated case at {case_dir}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
