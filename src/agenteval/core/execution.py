from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from agenteval.dataset.generator import generate_case  # noqa: F401  # re-export


def build_demo_trace(user_input: str, task_id: str = "demo_case") -> Dict[str, Any]:
    """
    Generate a minimal schema-compatible trace from a demo agent execution.
    """

    started_at = int(time.time() * 1000)

    steps: List[Dict[str, Any]] = [
        {
            "step_id": "step-1",
            "type": "thought",
            "actor_id": "demo-agent",
            "content": f"The agent received the input: {user_input}",
        },
        {
            "step_id": "step-2",
            "type": "tool_call",
            "actor_id": "demo-agent",
            "content": f"Calling search tool for query: {user_input}",
            "tool_name": "search",
            "tool_input": {"query": user_input},
        },
        {
            "step_id": "step-3",
            "type": "observation",
            "actor_id": "search-tool",
            "content": f"Mock search results for: {user_input}",
            "tool_output": {"results": [f"Mock search results for: {user_input}"]},
        },
        {
            "step_id": "step-4",
            "type": "final_answer",
            "actor_id": "demo-agent",
            "content": "The capital of France is Paris.",
        },
    ]

    finished_at = int(time.time() * 1000)

    return {
        "run_id": str(uuid.uuid4()),
        "task_id": task_id,
        "user_prompt": user_input,
        "model_version": "demo-agent-v1",
        "steps": steps,
        "metadata": {
            "timestamp": str(started_at),
            "latency_ms": finished_at - started_at,
        },
    }


def save_trace(trace: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(trace, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def save_prompt(user_input: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(user_input.strip() + "\n", encoding="utf-8")


def build_expected_outcome(case_id: str, severity: str = "Low") -> str:
    """
    Generate a minimal expected_outcome.md compatible with the existing runner.
    """
    return (
        "---\n"
        f"Case ID: {case_id}\n"
        "Primary Failure: None\n"
        "Secondary Failures:\n"
        f"Severity: {severity}\n"
        "---\n\n"
        "Demo case for generated trace.\n"
    )


def save_expected_outcome(case_id: str, output_path: Path, severity: str = "Low") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_expected_outcome(case_id=case_id, severity=severity),
        encoding="utf-8",
    )


def create_demo_case(
    case_id: str,
    user_input: str,
    base_dir: Path,
    severity: str = "Low",
) -> Path:
    """
    Create a full dataset case directory with:
    - prompt.txt
    - trace.json
    - expected_outcome.md
    """
    case_dir = base_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    trace = build_demo_trace(user_input=user_input, task_id=case_id)

    save_prompt(user_input, case_dir / "prompt.txt")
    save_trace(trace, case_dir / "trace.json")
    save_expected_outcome(case_id, case_dir / "expected_outcome.md", severity=severity)

    return case_dir
