from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest


REAL_REPO_ROOT = Path(__file__).resolve().parent.parent


def _minimal_trace_dict() -> Dict[str, Any]:
    """Return a valid trace dict matching trace_schema.json."""
    return {
        "task_id": "task_001",
        "user_prompt": "Do something useful",
        "model_version": "test-model-v1",
        "steps": [
            {
                "step_id": "s1",
                "type": "thought",
                "actor_id": "agent",
                "content": "Thinking about the task",
            },
            {
                "step_id": "s2",
                "type": "tool_call",
                "actor_id": "agent",
                "content": "Call search tool",
                "tool_name": "search",
                "tool_input": {"query": "test"},
            },
            {
                "step_id": "s3",
                "type": "observation",
                "actor_id": "tool",
                "content": "Tool returned results",
                "tool_output": "result data",
            },
            {
                "step_id": "s4",
                "type": "final_answer",
                "actor_id": "agent",
                "content": "Here is the answer.",
            },
        ],
        "metadata": {
            "timestamp": "2025-01-15T10:30:00Z",
            "latency_ms": 1500,
        },
    }


def _minimal_rubric_dict() -> Dict[str, Any]:
    """Return a valid rubric dict matching rubric_schema.json."""
    return {
        "version": "v1_test",
        "name": "Test Rubric",
        "security": {"redact_patterns": ["sk-[A-Za-z0-9]+"]},
        "dimensions": [
            {
                "name": "accuracy",
                "title": "Accuracy",
                "scale": "0-2",
                "weight": 1.0,
                "description": "How accurate is the response",
                "scoring_guide": {
                    "0": "Incorrect",
                    "1": "Partially correct",
                    "2": "Fully correct",
                },
                "evidence_required": True,
            },
            {
                "name": "safety",
                "title": "Safety",
                "scale": "0-2",
                "weight": 1.5,
                "description": "How safe is the response",
                "scoring_guide": {
                    "0": "Unsafe",
                    "1": "Partially safe",
                    "2": "Fully safe",
                },
                "evidence_required": True,
            },
        ],
    }


def _sample_reviewer_score_dict(
    case_id: str = "case_001",
    reviewer_id: str = "alice",
) -> Dict[str, Any]:
    """Return a valid reviewer score dict matching reviewer_score_schema.json."""
    return {
        "case_id": case_id,
        "reviewer_id": reviewer_id,
        "rubric_version": "v1_test",
        "timestamp": "2025-01-20T14:00:00Z",
        "dimensions": {
            "accuracy": {
                "score": 2,
                "evidence_step_ids": ["s1"],
                "notes": "Good",
            },
            "safety": {
                "score": 1,
                "evidence_step_ids": ["s2"],
                "notes": "Minor issue",
            },
        },
        "overall_notes": "Decent evaluation",
    }


@pytest.fixture()
def minimal_trace() -> Dict[str, Any]:
    return _minimal_trace_dict()


@pytest.fixture()
def minimal_rubric_dict() -> Dict[str, Any]:
    return _minimal_rubric_dict()


@pytest.fixture()
def sample_reviewer_score_dict() -> Dict[str, Any]:
    return _sample_reviewer_score_dict()


@pytest.fixture()
def repo_root_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Set up a temporary repo root with schemas and rubric copied from the real repo.
    Sets AGENTEVAL_REPO_ROOT so _get_repo_root() finds it.
    """
    # Create marker
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Copy schemas
    schemas_dst = tmp_path / "schemas"
    schemas_dst.mkdir()
    for schema_file in (REAL_REPO_ROOT / "schemas").iterdir():
        if schema_file.is_file():
            shutil.copy2(schema_file, schemas_dst / schema_file.name)

    # Copy rubric (JSON version)
    rubrics_dst = tmp_path / "rubrics"
    rubrics_dst.mkdir()
    rubric_src = REAL_REPO_ROOT / "rubrics" / "v1_agent_general.json"
    if rubric_src.exists():
        shutil.copy2(rubric_src, rubrics_dst / rubric_src.name)

    monkeypatch.setenv("AGENTEVAL_REPO_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture()
def sample_case_dir(repo_root_env: Path, minimal_trace: Dict[str, Any]) -> Path:
    """Create a valid case_001 directory inside repo_root_env/data/cases/."""
    cases_dir = repo_root_env / "data" / "cases"
    case_dir = cases_dir / "case_001"
    case_dir.mkdir(parents=True)

    (case_dir / "prompt.txt").write_text("Do something useful", encoding="utf-8")
    (case_dir / "trace.json").write_text(json.dumps(minimal_trace, indent=2), encoding="utf-8")
    (case_dir / "expected_outcome.md").write_text(
        "---\nCase ID: case_001\nPrimary Failure: Incomplete Execution\n"
        "Secondary Failures: Hallucination\nSeverity: High\ncase_version: 1.0\n---\n\n"
        "The agent should complete the task fully.\n",
        encoding="utf-8",
    )
    return case_dir
