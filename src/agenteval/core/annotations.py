"""Annotation module: reviewer notes and auto-eval overlay for trace steps."""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import jsonschema  # type: ignore[import-untyped]

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within

_VALID_SEVERITIES = ("none", "low", "medium", "high")

# Lazy-cached schema
_SCHEMA: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _SCHEMA
    if _SCHEMA is None:
        repo_root = _get_repo_root()
        schema_path = repo_root / "schemas" / "annotation_schema.json"
        _SCHEMA = json.loads(schema_path.read_text(encoding="utf-8"))
    return _SCHEMA


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Annotation:
    """A reviewer note attached to a specific trace step."""

    annotation_id: str
    case_id: str
    step_id: str
    reviewer_id: str
    timestamp: str
    content: str
    severity: Literal["none", "low", "medium", "high"]


@dataclass(frozen=True)
class DimEvidence:
    """Derived evidence from one rubric dimension referencing a step."""

    dimension: str
    score: int | None
    notes: str
    evaluator_type: str


@dataclass(frozen=True)
class AutoEvalOverlay:
    """Runtime overlay derived from an auto_evaluation.json file."""

    step_evidence: dict[str, list[DimEvidence]]  # step_id → dims citing this step
    case_flags: list[DimEvidence]  # dims with scores but no step-level evidence


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _annotation_to_dict(ann: Annotation) -> dict[str, Any]:
    return {
        "annotation_id": ann.annotation_id,
        "case_id": ann.case_id,
        "step_id": ann.step_id,
        "reviewer_id": ann.reviewer_id,
        "timestamp": ann.timestamp,
        "content": ann.content,
        "severity": ann.severity,
    }


def _dict_to_annotation(d: dict[str, Any]) -> Annotation:
    return Annotation(
        annotation_id=d["annotation_id"],
        case_id=d["case_id"],
        step_id=d["step_id"],
        reviewer_id=d["reviewer_id"],
        timestamp=d["timestamp"],
        content=d["content"],
        severity=d["severity"],
    )


def _ann_file(case_id: str, repo_root: Path) -> Path:
    reports_dir = repo_root / "reports"
    path = reports_dir / f"{case_id}.annotations.json"
    _safe_resolve_within(repo_root, path)
    return path


def _read_ann_file(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return result


def _write_ann_file(path: Path, data: dict[str, Any]) -> None:
    schema = _load_schema()
    jsonschema.validate(instance=data, schema=schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Public CRUD API
# ---------------------------------------------------------------------------


def add_annotation(
    case_id: str,
    step_id: str,
    reviewer_id: str,
    content: str,
    severity: Literal["none", "low", "medium", "high"],
    repo_root: Path | None = None,
) -> Annotation:
    """Add a reviewer annotation to a trace step.

    Appends to the case's annotation file, creating it if absent.
    Validates all inputs and the resulting file against the JSON Schema.

    Raises:
        ValueError: if case_id, step_id, reviewer_id, or content is empty,
                    or if severity is not a valid value.
    """
    if not case_id:
        msg = "case_id must be non-empty"
        raise ValueError(msg)
    if not step_id:
        msg = "step_id must be non-empty"
        raise ValueError(msg)
    if not reviewer_id:
        msg = "reviewer_id must be non-empty"
        raise ValueError(msg)
    if not content:
        msg = "content must be non-empty"
        raise ValueError(msg)
    if severity not in _VALID_SEVERITIES:
        msg = f"severity must be one of {_VALID_SEVERITIES}, got {severity!r}"
        raise ValueError(msg)

    if repo_root is None:
        repo_root = _get_repo_root()

    annotation_id = f"ann_{secrets.token_hex(4)}"
    timestamp = datetime.now(timezone.utc).isoformat()

    ann = Annotation(
        annotation_id=annotation_id,
        case_id=case_id,
        step_id=step_id,
        reviewer_id=reviewer_id,
        timestamp=timestamp,
        content=content,
        severity=severity,
    )

    path = _ann_file(case_id, repo_root)

    if path.exists():
        data = _read_ann_file(path)
    else:
        data = {"case_id": case_id, "annotations": []}

    data["annotations"].append(_annotation_to_dict(ann))
    _write_ann_file(path, data)

    return ann


def get_annotations(case_id: str, repo_root: Path | None = None) -> list[Annotation]:
    """Load all annotations for a case, sorted by timestamp ascending.

    Returns an empty list if no annotation file exists.
    """
    if repo_root is None:
        repo_root = _get_repo_root()

    path = _ann_file(case_id, repo_root)
    if not path.exists():
        return []

    data = _read_ann_file(path)
    annotations = [_dict_to_annotation(d) for d in data.get("annotations", [])]
    return sorted(annotations, key=lambda a: a.timestamp)


def delete_annotation(
    case_id: str,
    annotation_id: str,
    repo_root: Path | None = None,
) -> bool:
    """Remove an annotation by ID.

    Returns True if deleted, False if not found or file does not exist.
    """
    if repo_root is None:
        repo_root = _get_repo_root()

    path = _ann_file(case_id, repo_root)
    if not path.exists():
        return False

    data = _read_ann_file(path)
    original_count = len(data.get("annotations", []))
    data["annotations"] = [
        a for a in data["annotations"] if a["annotation_id"] != annotation_id
    ]

    if len(data["annotations"]) == original_count:
        return False

    _write_ann_file(path, data)
    return True


# ---------------------------------------------------------------------------
# Auto-eval overlay
# ---------------------------------------------------------------------------


def build_auto_eval_overlay(auto_eval: dict[str, Any]) -> AutoEvalOverlay:
    """Derive an overlay from an auto_evaluation dict. Pure function — no I/O.

    Returns an AutoEvalOverlay with:
    - step_evidence: dict mapping step_id → list of DimEvidence that cite it
    - case_flags: list of DimEvidence for dimensions with scores but no step evidence
    """
    step_evidence: dict[str, list[DimEvidence]] = {}
    case_flags: list[DimEvidence] = []

    dimensions = auto_eval.get("dimensions", {})
    for dim_name, dim_data in dimensions.items():
        if not isinstance(dim_data, dict):
            continue

        evidence = DimEvidence(
            dimension=dim_name,
            score=dim_data.get("score"),
            notes=dim_data.get("notes", ""),
            evaluator_type=dim_data.get("evaluator_type", "rule"),
        )

        evidence_step_ids: list[str] = dim_data.get("evidence_step_ids", [])
        if evidence_step_ids:
            for step_id in evidence_step_ids:
                step_evidence.setdefault(step_id, []).append(evidence)
        else:
            case_flags.append(evidence)

    return AutoEvalOverlay(step_evidence=step_evidence, case_flags=case_flags)


def get_auto_eval_for_case(
    case_id: str,
    repo_root: Path | None = None,
) -> dict[str, Any] | None:
    """Load the best available auto_evaluation for a case.

    Checks reports/{case_id}.auto_evaluation.json first, then scans runs/*/
    for the most recently modified file.

    Returns:
        Loaded auto_evaluation dict, or None if none exists.
    """
    if repo_root is None:
        repo_root = _get_repo_root()

    # Primary: reports/ directory
    reports_path = repo_root / "reports" / f"{case_id}.auto_evaluation.json"
    try:
        _safe_resolve_within(repo_root, reports_path)
        if reports_path.exists():
            loaded: dict[str, Any] = json.loads(reports_path.read_text(encoding="utf-8"))
            return loaded
    except (ValueError, OSError):
        pass

    # Fallback: most recent run directory
    runs_dir = repo_root / "runs"
    if not runs_dir.exists():
        return None

    best_path: Path | None = None
    best_mtime: float = -1.0

    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue
        candidate = run_dir / f"{case_id}.auto_evaluation.json"
        try:
            _safe_resolve_within(repo_root, candidate)
            if candidate.exists():
                mtime = candidate.stat().st_mtime
                if mtime > best_mtime:
                    best_mtime = mtime
                    best_path = candidate
        except (ValueError, OSError):
            continue

    if best_path is not None:
        result: dict[str, Any] = json.loads(best_path.read_text(encoding="utf-8"))
        return result

    return None
