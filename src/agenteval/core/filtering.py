"""Case filtering logic for selective evaluation.

Provides filter_cases(), derive_structural_tags(), and get_dataset_tags()
for narrowing the evaluation dataset before scoring.

All criteria are combined with AND logic (intersection). Tags are derived
live from trace.json at call time — no pre-indexing or sidecar files.
Pattern matching uses fnmatch (glob syntax, not regex).
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agenteval.schemas.trace import Trace


# ---------------------------------------------------------------------------
# Structural tag derivation
# ---------------------------------------------------------------------------


def derive_structural_tags(trace: Trace) -> tuple[str, ...]:
    """Derive structural tags from trace steps.

    Returns a tuple of applicable tag strings:
    - ``has_tool_calls``: trace contains at least one ``tool_call`` step
    - ``multi_step``: trace contains more than 3 steps
    - ``has_final_answer``: trace contains at least one ``final_answer`` step
    """
    steps = trace.get("steps", [])
    tags: list[str] = []

    if any(s.get("type") == "tool_call" for s in steps):
        tags.append("has_tool_calls")
    if len(steps) > 3:
        tags.append("multi_step")
    if any(s.get("type") == "final_answer" for s in steps):
        tags.append("has_final_answer")

    return tuple(tags)


# ---------------------------------------------------------------------------
# Dataset tag collection
# ---------------------------------------------------------------------------


def get_dataset_tags(case_dirs: list[Path]) -> set[str]:
    """Return the union of all tags across all cases in the dataset.

    Loads trace.json for each case, calls tag_trace() and derive_structural_tags(),
    and returns the union of all tags. Unreadable or missing cases are skipped.

    Used by the UI to populate the tag filter dropdown.
    """
    from agenteval.core.tagger import tag_trace

    all_tags: set[str] = set()
    for case_dir in case_dirs:
        trace_path = case_dir / "trace.json"
        if not trace_path.exists():
            continue
        try:
            raw = json.loads(trace_path.read_text(encoding="utf-8"))
            failure_tags = tag_trace(raw)
            structural_tags = derive_structural_tags(raw)
            all_tags.update(failure_tags)
            all_tags.update(structural_tags)
        except Exception:  # noqa: BLE001
            continue

    return all_tags


# ---------------------------------------------------------------------------
# Case filtering
# ---------------------------------------------------------------------------


def _read_case_metadata(case_dir: Path) -> dict[str, str]:
    """Parse YAML front matter from expected_outcome.md. Returns {} on failure."""
    outcome_path = case_dir / "expected_outcome.md"
    if not outcome_path.exists():
        return {}
    try:
        text = outcome_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}
        meta: dict[str, str] = {}
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "---":
                break
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                meta[key.strip().lower().replace(" ", "_")] = value.strip()
        return meta
    except Exception:  # noqa: BLE001
        return {}


def filter_cases(
    case_dirs: list[Path],
    case_ids: list[str] | None = None,
    failure_type: str | None = None,
    severity: list[str] | None = None,
    tags: list[str] | None = None,
    pattern: str | None = None,
) -> list[Path]:
    """Return case_dirs matching all non-None criteria (AND logic / intersection).

    Args:
        case_dirs: Full list of candidate case directories.
        case_ids: If non-empty, return only dirs whose name is in this list.
            All other filter args are ignored when case_ids is specified.
        failure_type: Case-insensitive match against ``primary_failure`` in
            ``expected_outcome.md`` front matter.
        severity: Case-insensitive membership test against ``severity`` in
            ``expected_outcome.md`` front matter. Case must match any value.
        tags: The case must have ALL listed tags (derived live from trace.json).
        pattern: Glob pattern matched against ``case_dir.name`` via fnmatch.

    Returns:
        Filtered list of case directories. Returns empty list (not an error)
        when no cases match. Cases where trace.json or expected_outcome.md is
        missing/unreadable are skipped silently when a filter requires them.
    """
    # Explicit case_ids short-circuits all other filters
    if case_ids:
        id_set = set(case_ids)
        return [d for d in case_dirs if d.name in id_set]

    # No filters at all — return everything
    if failure_type is None and severity is None and tags is None and pattern is None:
        return list(case_dirs)

    from agenteval.core.tagger import tag_trace

    result: list[Path] = []
    for case_dir in case_dirs:
        # --- glob pattern ---
        if pattern is not None and not fnmatch.fnmatch(case_dir.name, pattern):
            continue

        # --- metadata-based filters (failure_type, severity) ---
        if failure_type is not None or severity is not None:
            meta = _read_case_metadata(case_dir)
            if failure_type is not None:
                case_failure = meta.get("primary_failure", "")
                if case_failure.lower() != failure_type.lower():
                    continue
            if severity is not None:
                case_sev = meta.get("severity", "").strip()
                if case_sev.lower() not in [s.lower() for s in severity]:
                    continue

        # --- tag-based filter (live from trace.json) ---
        if tags is not None:
            trace_path = case_dir / "trace.json"
            if not trace_path.exists():
                continue
            try:
                raw = json.loads(trace_path.read_text(encoding="utf-8"))
                case_tags: set[str] = set(tag_trace(raw)) | set(derive_structural_tags(raw))
                if not all(t in case_tags for t in tags):
                    continue
            except Exception:  # noqa: BLE001
                continue

        result.append(case_dir)

    return result
